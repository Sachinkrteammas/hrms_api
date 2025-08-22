from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.user import User, CompanyUser
from schemas.common import BaseResponse
from dependencies.auth import get_current_admin_user

# router = APIRouter()

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import CompanyUser, Candidate, Company  # Ensure all models are imported
from models.candidate import Candidate



router = APIRouter()

def start_of_day(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day)

# Normalize backend status names to frontend-friendly ones
# - None/UNKNOWN -> PENDING
# - COMPLETED -> VERIFIED
# - Keep SUBMITTED/IN_PROGRESS/REJECTED/REQUESTED as-is

def normalize_status(status_name: str | None) -> str:
    if not status_name or status_name.upper() == "UNKNOWN":
        return "PENDING"
    upper = status_name.upper()
    if upper == "COMPLETED":
        return "VERIFIED"
    return upper

def calculate_tow_time(candidate) -> str:
    """Calculate Time of Work (TOW) based on employment history and verification time"""
    try:
        # Calculate work experience component (70% weight)
        work_experience_score = 0
        if candidate.employments and len(candidate.employments) > 0:
            total_years = 0
            for emp in candidate.employments:
                if emp.starts_from:
                    start_date = emp.starts_from
                    end_date = emp.ends_at if emp.ends_at else datetime.utcnow().date()
                    
                    # Calculate years between start and end
                    years = (end_date - start_date).days / 365.25
                    total_years += years
            
            # Convert years to percentage (assuming 10+ years = 100%)
            if total_years >= 10:
                work_experience_score = 100
            elif total_years <= 0:
                work_experience_score = 0
            else:
                work_experience_score = int((total_years / 10) * 100)
        else:
            work_experience_score = 0
        
        # Calculate verification time component (30% weight)
        verification_time_score = 0
        if candidate.created_at:
            # Calculate days since candidate was created
            days_since_creation = (datetime.utcnow().date() - candidate.created_at.date()).days
            
            # If verification completed within 7 days = 100%, if > 30 days = 0%
            if days_since_creation <= 7:
                verification_time_score = 100
            elif days_since_creation >= 30:
                verification_time_score = 0
            else:
                verification_time_score = int(((30 - days_since_creation) / 23) * 100)
        else:
            verification_time_score = 50  # Default if no creation date
        
        # Calculate weighted average
        final_score = int((work_experience_score * 0.7) + (verification_time_score * 0.3))
        
        return f"{final_score}%"
            
    except Exception as e:
        print(f"Error calculating TOW time: {e}")
        return "25%"  # Default fallback

@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard data for admin"""
    # 1. Find company for current user
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            # status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )

    company_id = company_user.company_id

    # 2. Get credits
    company = db.query(Company).filter(Company.id == company_id).first()
    credits = company.credits if company else 0

    # 3. Get all candidates of the company
    candidates = db.query(Candidate).filter(
        Candidate.company_id == company_id,
        Candidate.is_shadowed == False
    ).all()

    total_candidates = len(candidates)

    # Normalize statuses for all candidates
    normalized_statuses = [
        normalize_status(c.verification_status.name if c.verification_status else None)
        for c in candidates
    ]

    # 4. Verification status counts
    pending_verification = sum(1 for s in normalized_statuses if s in {"PENDING", "SUBMITTED", "IN_PROGRESS"})
    completed_verification = sum(1 for s in normalized_statuses if s == "VERIFIED")

    # 5. Weekly verification data (based on VERIFIED/COMPLETED mapped to VERIFIED)
    today = start_of_day(datetime.utcnow())
    verification_data = []

    for i in range(7):
        day = today - timedelta(days=i)
        count = sum(
            1 for c in candidates
            if normalize_status(c.verification_status.name if c.verification_status else None) == "VERIFIED"
            and c.updated_at and start_of_day(c.updated_at) == day
        )
        verification_data.append({
            "date": day.strftime('%Y-%m-%d'),
            "count": count
        })

    verification_data.reverse()

    # 6. Recent candidates
    recent_candidates = sorted(candidates, key=lambda x: x.updated_at or datetime.min, reverse=True)[:5]
    recent_candidates_data = [
        {
            "id": c.id,
            "name": f"{c.first_name} {c.last_name}".strip(),
            "status": normalize_status(c.verification_status.name if c.verification_status else None),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in recent_candidates
    ]

    # 7. Status distribution
    status_distribution: dict[str, int] = {}
    for s in normalized_statuses:
        status_distribution[s] = status_distribution.get(s, 0) + 1

    # 8. Final response
    return {
        "credits": credits,
        "total_candidates": total_candidates,
        "pending_verification": pending_verification,
        "completed_verification": completed_verification,
        "verification_data": verification_data,
        "recent_candidates": recent_candidates_data,
        "status_distribution": status_distribution
    }



@router.get("/reports")
async def get_admin_reports(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin reports"""
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    # Fetch candidates for this company
    candidates = db.query(Candidate).filter(
        Candidate.company_id == company_user.company_id,
        Candidate.is_shadowed == False
    ).all()

    # Build report list items expected by frontend
    def compute_score(c: Candidate) -> int:
        scores = []
        if getattr(c, "report_identity", None) and c.report_identity.score is not None:
            scores.append(c.report_identity.score)
        if getattr(c, "report_court_check", None) and c.report_court_check.score is not None:
            scores.append(c.report_court_check.score)
        if getattr(c, "report_aml", None) and c.report_aml.score is not None:
            scores.append(c.report_aml.score)
        if getattr(c, "report_bank_account", None) and c.report_bank_account.score is not None:
            scores.append(c.report_bank_account.score)
        if scores:
            return int(sum(scores) / len(scores))
        return int(c.score) if c.score is not None else 0

    report_items = [
        {
            "id": c.id,
            "firstName": c.first_name or "",
            "lastName": c.last_name or "",
            "phone": c.phone or "",
            "email": c.email or "",
            "image": c.image,
            "createdAt": (c.created_at.isoformat() if c.created_at else datetime.utcnow().isoformat()),
            "status": normalize_status(c.verification_status.name if c.verification_status else None),
            "score": compute_score(c),
        }
        for c in candidates
    ]

    # Sort by createdAt desc
    report_items.sort(key=lambda x: x["createdAt"], reverse=True)

    return {"reports": report_items}



@router.get("/report/{candidate_id}")
async def get_admin_report_detail(
    candidate_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get report detail for a candidate"""
    # Ensure user belongs to company
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not associated with any company")

    c: Candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.company_id == company_user.company_id
    ).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Build minimal structure matching frontend ReportDataModel
    dob_str = c.dob.isoformat() if c.dob else (getattr(getattr(c, "aadhar_details", None), "dob", "") or "")
    report = {
        "identityData": {
            "isApplicable": True,
            "isIdentityVerified": True,
            "impact": "Low",
            "score": c.report_identity.score if getattr(c, "report_identity", None) and c.report_identity.score is not None else 100,
            "weightage": "25%",
            "status": normalize_status(c.verification_status.name if c.verification_status else None),
            "isAadharVerified": True,
            "isDobVerified": True,
            "isFatherNameVerified": True,
            "isGenderVerified": True,
            "isNameVerified": True,
            "isPanVerified": True,
            "currentAddressCheckScore": 100,
            "permanentAddressCheckScore": 100,
            "towTime": calculate_tow_time(c),  # Time of Work/Time on Work metric
        },
        "employmentData": {
        "isApplicable": True,
        "impact": "Low",
        "status": normalize_status(
            c.report_employment.verification_status.name
            if getattr(c, "report_employment", None)
               and getattr(c.report_employment, "verification_status", None)
            else None
        ),
        "towTime": calculate_tow_time(c),
        "data": (
            getattr(c.report_employment, "data", None)
            if getattr(c, "report_employment", None)
            else None
        )
        or (
            (getattr(c.report_employment, "apis", {}) or {}).get("employment_history")
            if getattr(c, "report_employment", None)
            else None
        )
        or {"result": [], "status": 200, "message": "Verified"},
    },



        "courtData": {
            "isApplicable": True,
            "score": c.report_court_check.score if getattr(c, "report_court_check", None) and c.report_court_check.score is not None else 100,
            "impact": "Low",
            "weightage": "25%",
            "status": normalize_status(c.verification_status.name if c.verification_status else None),
            "data": (getattr(c.report_court_check, "data", None) if getattr(c, "report_court_check", None) else None)
                or ((getattr(c.report_court_check, "apis", {}) or {}).get("court_search") if getattr(c, "report_court_check", None) else None)
                or {"total": 0, "status": 200, "pdfName": "", "cases": []},
        },
        "amlData": {
            "isApplicable": True,
            "score": c.report_aml.score if getattr(c, "report_aml", None) and c.report_aml.score is not None else 100,
            "impact": "Low",
            "weightage": "25%",
            "status": normalize_status(c.verification_status.name if c.verification_status else None),
            "data": {"Case_Outcome": {}, "entitychecks": []},
        },
        "bankAccountData": {
            "isApplicable": True,
            "impact": "Low",
            "score": c.report_bank_account.score if getattr(c, "report_bank_account", None) and c.report_bank_account.score is not None else 100,
            "weightage": "25%",
            "status": normalize_status(c.verification_status.name if c.verification_status else None),
            "data": {
                "status": 200,
                "message": "Verified",
                "ifscInfo": {},
                "bankRefNo": "",
                "nameMatchScore": 100,
                "beneficiaryName": (
                    # Use real beneficiary name from bank account (updated by external API)
                    getattr(c.bank_account, "name", None) if getattr(c, "bank_account", None) else None
                    # Fallback to report data if available
                    or (getattr(c.report_bank_account, "data", {}).get("beneficiaryName") if getattr(c, "report_bank_account", None) else None)
                    # Final fallback to candidate name
                    or f"{c.first_name} {c.last_name or ''}".strip()
                ),
                "nameMatchStatus": "MATCHED",
                "verificationStatus": "VERIFIED",
            },
        },
    }

    response = {
        "id": c.id,
        "firstName": c.first_name or "",
        "lastName": c.last_name or "",
        "phone": c.phone or "",
        "email": c.email or "",
        "image": c.image,
        "candidateCode": c.candidate_code,
        "score": int(c.score) if c.score is not None else 100,
        "verificationStatus": {"name": normalize_status(c.verification_status.name if c.verification_status else None)},
        "towTime": calculate_tow_time(c),  # Time of Work/Time on Work metric
        "bankAccount": {
            "accountNo": getattr(c.bank_account, "account_no", None) if getattr(c, "bank_account", None) else None,
            "ifsc": getattr(c.bank_account, "ifsc", None) if getattr(c, "bank_account", None) else None,
        },
        "lastAction": None,
        "middleName": c.middle_name,
        "gender": str(c.gender.name) if c.gender else "",
        "dob": dob_str,
        "fatherName": c.father_name or "",
        "motherName": c.mother_name or "",
        "maritalStatus": c.marital_status or "",
        "alternatePhone": c.alternate_phone or "",
        "uan": c.uan or "",
        "nid": {
            "photo": getattr(c.nid, "photo", "") if getattr(c, "nid", None) else "",
            "aadhar": getattr(c.nid, "aadhar", "") if getattr(c, "nid", None) else "",
            "pan": getattr(c.nid, "pan", "") if getattr(c, "nid", None) else "",
            "passport": getattr(c.nid, "passport", "") if getattr(c, "nid", None) else "",
            "aadharNo": getattr(c.nid, "aadhar_no", "") if getattr(c, "nid", None) else "",
            "uanNo": getattr(c.nid, "uan_no", "") if getattr(c, "nid", None) else "",
            "panNo": getattr(c.nid, "pan_no", "") if getattr(c, "nid", None) else "",
        },
        "address": [
            {
                "inIndia": getattr(addr, "in_india", False),
                "houseNo": getattr(addr, "house_no", ""),
                "locality": getattr(addr, "locality", ""),
                "residencyName": getattr(addr, "residency_name", ""),
                "city": getattr(addr, "city", ""),
                "state": getattr(addr, "state", ""),
                "pincode": getattr(addr, "pincode", ""),  # This maps to pin_code in DB
                "landmark": getattr(addr, "landmark", ""),
                "residingFrom": addr.residing_from.isoformat() if getattr(addr, "residing_from", None) else "",
                "residencyProof": getattr(addr, "residency_proof", ""),
                "isCurrent": getattr(addr, "is_current", False),
            }
            for addr in (c.address or [])
        ],
        "isFresher": len(c.employments or []) == 0,
        "educations": [
            {
                "university": getattr(ed, "university", ""),
                "degree": getattr(ed, "degree", ""),
                "course": getattr(ed, "course", ""),
                "idNumber": getattr(ed, "id_number", ""),
                "grade": getattr(ed, "grade", ""),
                "college": getattr(ed, "college", ""),
                "country": getattr(ed, "country", ""),
                "state": getattr(ed, "state", ""),
                "city": getattr(ed, "city", ""),
                "markSheet": getattr(ed, "mark_sheet", ""),
                "certificate": getattr(ed, "certificate", ""),
            }
            for ed in (c.educations or [])
        ],
        "employments": [
            {
                "company": getattr(emp, "company", ""),
                "designation": getattr(emp, "designation", ""),
                "city": getattr(emp, "city", ""),
                "phone": getattr(emp, "phone", ""),
                "email": getattr(emp, "email", ""),
                "address": getattr(emp, "address", ""),
                "employeeType": getattr(emp, "employee_type", ""),
                "department": getattr(emp, "department", ""),
                "startsFrom": emp.starts_from.isoformat() if getattr(emp, "starts_from", None) else "",
                "endsAt": emp.ends_at.isoformat() if getattr(emp, "ends_at", None) else "",
                "currentlyWorking": bool(getattr(emp, "currently_working", False)),
                "salary": getattr(emp, "salary", 0) or 0,
                "uan": getattr(emp, "uan", ""),
                "employeeCode": getattr(emp, "employee_code", ""),
                "band": getattr(emp, "band", ""),
                "remark": getattr(emp, "remark", ""),
            }
            for emp in (c.employments or [])
        ],
        "bankAccount": {
            "accountNo": getattr(c.bank_account, "account_no", "") if c.bank_account else "",
            "ifsc": getattr(c.bank_account, "ifsc", "") if c.bank_account else "",
            "name": getattr(c.bank_account, "name", "") if c.bank_account else ""
        },
        "report": report,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else datetime.utcnow().isoformat(),
        "subscription": {"id": 1, "name": "Basic"},
        "services": [],
    }

    return response






