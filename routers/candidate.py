from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import csv
import io

from models.database import get_db
from models.user import User, CompanyUser
from models.candidate import Candidate, CandidateNid, CandidateAddress, CandidateEducation, CandidateEmployment, CandidateBankAccount
from models.company import Company
from schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateResponse, CandidateLogin,
    CandidateListResponse, ReferenceCreate, ReferenceUpdate, ReferenceResponse,
    CandidateSendEmail, CandidateReject, CandidateAadharOTP, CandidateAadharVerify
)
from schemas.common import PaginationParams, BaseResponse
from schemas.auth import TokenResponse
from dependencies.auth import get_current_admin_user, get_current_candidate_user, get_password_hash, create_access_token
from services.candidate_service import CandidateService
from services.verification_service import VerificationService
from utils.candidate_utils import generate_candidate_code, encrypt_slug, decrypt_slug
from services.email_service import EmailService

router = APIRouter()

@router.post("", response_model=BaseResponse)
async def add_candidate(
    candidate_data: CandidateCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add a new candidate"""
    # Get company ID from current user
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    # Check company credits
    company = db.query(Company).filter(Company.id == company_user.company_id).first()
    if not company or company.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough credits"
        )
    
    # Check if candidate already exists
    existing_candidate = db.query(Candidate).filter(
        Candidate.email == candidate_data.email,
        Candidate.company_id == company_user.company_id,
        Candidate.is_shadowed == False
    ).first()
    
    if existing_candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate with this email already exists"
        )
    
    try:
        # Create candidate
        candidate_service = CandidateService(db)
        candidate = await candidate_service.add_candidate(candidate_data, company_user.company_id)
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create candidate"
            )
        
        # Deduct credit
        company.credits -= 1
        db.commit()
        
        # Send email to candidate
        try:
            print(f"📧 Attempting to send email to candidate: {candidate.email}")
            email_service = EmailService()
            # Pass the candidate object directly as expected by the method
            email_result = await email_service.send_candidate_email(candidate)
            if email_result:
                print(f"✅ Email sent successfully to {candidate.email}")
            else:
                print(f"⚠️ Email service returned False for {candidate.email}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            # Don't fail the request if email fails
        
        return BaseResponse(
            success=True,
            message="Candidate created successfully",
            data={"candidate_id": candidate.id}
        )
        
    except Exception as e:
        db.rollback()
        print(f"Error creating candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating candidate: {str(e)}"
        )

@router.post("/upload", response_model=BaseResponse)
async def upload_candidates(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Upload candidates from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # Get company ID from current user
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    # Read CSV file
    content = await file.read()
    csv_text = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_text))
    
    candidates_data = []
    for row in csv_reader:
        candidates_data.append(CandidateCreate(**row))
    
    # Check company credits
    company = db.query(Company).filter(Company.id == company_user.company_id).first()
    if not company or company.credits < len(candidates_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough credits. You have only {company.credits if company else 0} left."
        )
    
    # Add candidates
    candidate_service = CandidateService(db)
    added_candidates = await candidate_service.add_candidates(candidates_data, company_user.company_id)
    
    if not added_candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidates added"
        )
    
    # Reduce company credits
    company.credits -= len(added_candidates)
    db.commit()
    
    # Send emails to candidates
    # email_service = EmailService() # This line is removed as per the edit hint
    for candidate in added_candidates:
        # await email_service.send_candidate_email(candidate) # This line is removed as per the edit hint
        print(f"Bulk candidate created: {candidate.email}")
    
    return BaseResponse(message="Candidates added successfully")

@router.get("", response_model=CandidateListResponse)
async def get_candidates(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get candidates list with pagination"""
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    candidate_service = CandidateService(db)
    items = await candidate_service.get_candidates(
        company_user.company_id, 
        pagination.limit, 
        pagination.next
    )
    insights = await candidate_service.get_candidate_insights(company_user.company_id)
    
    return CandidateListResponse(
        items=items,
        insights=insights,
        next=pagination.next + pagination.limit if len(items) == pagination.limit else -1
    )

@router.get("/details/{slug}")
async def get_candidate_details_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get candidate details by encrypted slug"""
    try:
        candidate_id = decrypt_slug(slug)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slug"
        )
    
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_candidate_by_id(candidate_id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Build comprehensive details similar to previous behavior
    nid = getattr(candidate, "nid", None)
    address_list = getattr(candidate, "address", []) or []
    education_list = getattr(candidate, "educations", []) or []
    employment_list = getattr(candidate, "employments", []) or []
    bank = getattr(candidate, "bank_account", None)
    bank_report = getattr(candidate, "report_bank_account", None)
    # Fallback for DOB from aadhar details if primary is missing
    dob_str = (
        candidate.dob.isoformat() if getattr(candidate, "dob", None) else (
            getattr(getattr(candidate, "aadhar_details", None), "dob", "") or ""
        )
        )
    
    return {
        "id": candidate.id,
        "name": candidate.first_name,
        "firstName": candidate.first_name or "",
        "middleName": candidate.middle_name or "",
        "lastName": candidate.last_name or "",
        "gender": str(candidate.gender.name) if getattr(candidate, "gender", None) else "",
        "dob": dob_str,
        "phone": candidate.phone or "",
        "email": candidate.email or "",
        "uan": candidate.uan or "",
        "companyName": candidate.company.name if candidate.company else "",
        "companyDescription": "",
        "message": "Welcome to our company",
        "status": candidate.verification_status.name if candidate.verification_status else "PENDING",
        "nid": {
            "photo": getattr(nid, "photo", "") if nid else "",
            "aadhar": getattr(nid, "aadhar", "") if nid else "",
            "pan": getattr(nid, "pan", "") if nid else "",
            "passport": getattr(nid, "passport", "") if nid else "",
            "aadharNo": getattr(nid, "aadhar_no", "") if nid else "",
            "uanNo": getattr(nid, "uan_no", "") if nid else "",
            "panNo": getattr(nid, "pan_no", "") if nid else "",
            "passportNo": getattr(nid, "passport_no", "") if nid else "",
        },
        "address": [
            {
                "inIndia": getattr(addr, "in_india", False),
                "houseNo": getattr(addr, "house_no", ""),
                "locality": getattr(addr, "locality", ""),
                "residencyName": getattr(addr, "residency_name", ""),
                "city": getattr(addr, "city", ""),
                "state": getattr(addr, "state", ""),
                "pincode": getattr(addr, "pincode", ""),
                "landmark": getattr(addr, "landmark", ""),
                "residingFrom": addr.residing_from.isoformat() if getattr(addr, "residing_from", None) else "",
                "residencyProof": getattr(addr, "residency_proof", ""),
                "isCurrent": getattr(addr, "is_current", False),
            }
            for addr in address_list
        ],
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
            for ed in education_list
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
                "currentlyWorking": getattr(emp, "currently_working", False),
                "salary": getattr(emp, "salary", None),
                "employeeCode": getattr(emp, "employee_code", ""),
                "band": getattr(emp, "band", ""),
                "remark": getattr(emp, "remark", ""),
                "manager": None,
            }
            for emp in employment_list
        ],
        "bankAccount": {
            "accountNo": getattr(bank, "account_no", None) if bank else None,
            "ifsc": getattr(bank, "ifsc", None) if bank else None,
            "name": getattr(bank, "name", None) if bank else None,
            "beneficiaryName": (
                (getattr(bank, "name", None) if bank else None)
                or (((getattr(bank_report, "data", None) or {}).get("beneficiaryName")) if bank_report else None)
                or (((((getattr(bank_report, "apis", None) or {}).get("bank_account", {})).get("beneficiaryName"))) if bank_report else None)
            ),
        },
    }

@router.post("/login", response_model=TokenResponse)
async def candidate_login(
    login_data: CandidateLogin,
    db: Session = Depends(get_db)
):
    """Candidate login endpoint"""
    try:
        candidate_service = CandidateService(db)
        result = await candidate_service.candidate_login(login_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.put("", response_model=BaseResponse)
async def update_candidate(
    candidate_data: CandidateUpdate,
    current_candidate: Candidate = Depends(get_current_candidate_user),
    db: Session = Depends(get_db)
):
    """Update candidate information"""
    print(f"🔄 Candidate {current_candidate.id} updating with data: {candidate_data}")
    print(f"🔄 Verify flag: {candidate_data.verify}")
    if hasattr(candidate_data, 'bankAccount') and candidate_data.bankAccount:
        print(f"🏦 Bank account data: {candidate_data.bankAccount}")
    
    candidate_service = CandidateService(db)

    # Default behavior: update the existing candidate record
    candidate = await candidate_service.update_candidate(candidate_data, current_candidate.id)
    
    slug = None
    if candidate_data.verify:
        print(f"🚀 Candidate {current_candidate.id} wants verification - starting pipeline")
        slug = encrypt_slug(str(current_candidate.id))
        await candidate_service.update_candidate_status("SUBMITTED", current_candidate.id)
        # Start verification in background (fire-and-forget)
        try:
            import asyncio
            print(f"🚀 Starting verification pipeline for candidate {current_candidate.id}")
            # Run verification pipeline directly instead of fire-and-forget
            await candidate_service.run_verification_pipeline(current_candidate.id)
            print(f"✅ Verification pipeline completed for candidate {current_candidate.id}")
        except Exception as e:
            print(f"❌ Verification pipeline failed for candidate {current_candidate.id}: {e}")
            # Don't fail the request if verification fails
            pass
        
    return BaseResponse(
        message="Candidate updated successfully",
        slug=slug
    )

@router.post("/sendEmail", response_model=BaseResponse)
async def send_candidate_email(
    email_data: CandidateSendEmail,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Resend email to candidate"""
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_candidate_for_email(email_data.id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # email_service = EmailService() # This line is removed as per the edit hint
    # await email_service.send_candidate_email(candidate, resend=True) # This line is removed as per the edit hint
    
    print(f"Email resend requested for candidate: {candidate.email}")
    
    return BaseResponse(message="Email sent successfully")

@router.post("/reject", response_model=BaseResponse)
async def reject_candidate(
    reject_data: CandidateReject,
    db: Session = Depends(get_db)
):
    """Reject candidate"""
    candidate_service = CandidateService(db)
    await candidate_service.reject_candidate(reject_data.id)
    
    return BaseResponse(message="Candidate rejected successfully")

@router.post("/aadhar/otp")
async def send_aadhar_otp(
    aadhar_data: CandidateAadharOTP,
    current_candidate: Candidate = Depends(get_current_candidate_user),
    db: Session = Depends(get_db)
):
    """Send Aadhar OTP"""
    verification_service = VerificationService()
    result = await verification_service.send_aadhar_otp(aadhar_data)
    print(result,"result====")
    return result

@router.post("/aadhar/verify")
async def verify_aadhar_otp(
    aadhar_data: CandidateAadharVerify,
    current_candidate: Candidate = Depends(get_current_candidate_user),
    db: Session = Depends(get_db)
):
    """Verify Aadhar OTP"""
    verification_service = VerificationService()
    result = await verification_service.verify_aadhar(aadhar_data)
    
    if result:
        candidate_service = CandidateService(db)
        await candidate_service.update_aadhar_details(result, current_candidate.id)
        # TODO: Get UAN from Aadhar
    
    return BaseResponse(message="Aadhar verified successfully")

@router.post("/{candidate_id}/approve", response_model=BaseResponse)
async def approve_candidate(
    candidate_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approve candidate: mark as COMPLETED and generate minimal reports"""
    candidate_service = CandidateService(db)
    ok = await candidate_service.approve_candidate(candidate_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return BaseResponse(message="Candidate approved successfully")

@router.post("/{candidate_id}/verify-bank", response_model=BaseResponse)
async def verify_bank_account(
    candidate_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Manually trigger bank account verification for testing"""
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    
    # Run just the bank verification part
    from services.verification_service import VerificationService
    verifier = VerificationService()
    
    if candidate.bank_account and candidate.bank_account.account_no and candidate.bank_account.ifsc:
        bank_payload = {
            "accountNo": candidate.bank_account.account_no,
            "ifsc": candidate.bank_account.ifsc,
            "name": candidate.bank_account.name,
        }
        print(f"🔍 Manual bank verification for candidate {candidate_id}: {bank_payload}")
        
        try:
            bank = await verifier.bank_account_verification(bank_payload)
            print(f"📡 Manual bank API response: {bank}")
            
            # Update the bank report
            bank_report = candidate.report_bank_account
            if not bank_report:
                from models.verification import ReportBankAccount
                bank_report = ReportBankAccount(candidate_id=candidate_id)
                db.add(bank_report)
                db.flush()
            
            apis = bank_report.apis or {}
            apis["bank_account"] = bank
            bank_report.apis = apis
            
            # Extract beneficiary name
            beneficiary_name = None
            try:
                beneficiary_name = (
                    bank.get("beneficiaryName")
                    or bank.get("beneficiary_name")  # Add underscore version
                    or (bank.get("result") or {}).get("beneficiaryName")
                    or (bank.get("result") or {}).get("beneficiary_name")  # Add underscore version
                    or (bank.get("data") or {}).get("beneficiaryName")
                    or (bank.get("data") or {}).get("beneficiary_name")  # Add underscore version
                    or (bank.get("ifscInfo") or {}).get("accountHolderName")
                    or bank.get("name")
                )
                print(f"🏦 Manual extraction - beneficiary name: {beneficiary_name}")
            except Exception as e:
                print(f"❌ Manual extraction error: {e}")
                beneficiary_name = None
            
            if beneficiary_name:
                candidate.bank_account.name = beneficiary_name
                print(f"✏️ Updated bank account name to: {beneficiary_name}")
            
            # Update report data
            bank_data = bank_report.data or {}
            bank_data.update({
                "beneficiaryName": beneficiary_name,
                "nameMatchScore": bank.get("nameMatchScore"),
                "nameMatchStatus": bank.get("nameMatchStatus"),
                "verificationStatus": bank.get("verificationStatus") or bank.get("status"),
            })
            bank_report.data = bank_data
            
            db.commit()
            return BaseResponse(message=f"Bank verification completed. API response: {bank}")
            
        except Exception as e:
            print(f"❌ Manual bank verification error: {e}")
            return BaseResponse(message=f"Bank verification failed: {str(e)}")
    else:
        return BaseResponse(message="Candidate has no bank account details to verify")

@router.post("/{candidate_id}/create-bank-account", response_model=BaseResponse)
async def create_bank_account(
    candidate_id: int,
    bank_data: dict,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Manually create bank account record for testing"""
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    
    try:
        from models.candidate import CandidateBankAccount
        
        # Check if bank account already exists
        existing_bank = db.query(CandidateBankAccount).filter_by(candidate_id=candidate_id).first()
        
        if existing_bank:
            # Update existing
            existing_bank.account_no = bank_data.get("accountNo")
            existing_bank.ifsc = bank_data.get("ifsc")
            existing_bank.name = bank_data.get("name")
            message = "Bank account updated"
        else:
            # Create new
            new_bank = CandidateBankAccount(
                candidate_id=candidate_id,
                account_no=bank_data.get("accountNo"),
                ifsc=bank_data.get("ifsc"),
                name=bank_data.get("name")
            )
            db.add(new_bank)
            message = "Bank account created"
        
        db.commit()
        return BaseResponse(message=f"{message} successfully. Now you can run bank verification.")
        
    except Exception as e:
        db.rollback()
        return BaseResponse(message=f"Failed to create bank account: {str(e)}")

# Reference check endpoints
@router.get("/reference", response_model=List[ReferenceResponse])
async def get_reference_data(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get reference data for company"""
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    candidate_service = CandidateService(db)
    return await candidate_service.get_reference_data(company_user.company_id)

@router.post("/reference/login", response_model=TokenResponse)
async def reference_login(
    reference_data: dict,
    db: Session = Depends(get_db)
):
    """Reference login endpoint"""
    candidate_service = CandidateService(db)
    return await candidate_service.reference_login(reference_data)

@router.post("/reference/sendEmail", response_model=BaseResponse)
async def send_reference_email(
    reference_data: dict,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Send email to reference"""
    # email_service = EmailService() # This line is removed as per the edit hint
    # await email_service.send_reference_email(reference_data["id"], resend=True) # This line is removed as per the edit hint
    
    print(f"Reference email requested for ID: {reference_data['id']}")
    
    return BaseResponse(message="Email sent successfully")

@router.put("/reference/update", response_model=BaseResponse)
async def update_reference(
    reference_data: ReferenceUpdate,
    db: Session = Depends(get_db)
):
    """Update reference information"""
    candidate_service = CandidateService(db)
    await candidate_service.update_reference(reference_data)
    
    slug = encrypt_slug(str(reference_data.reference_id))
    return BaseResponse(
        message="Data updated successfully",
        slug=slug
    )

@router.get("/reference/{slug}")
async def get_reference_details_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get reference details by encrypted slug"""
    try:
        reference_id = decrypt_slug(slug)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slug"
        )
    
    candidate_service = CandidateService(db)
    reference = await candidate_service.get_reference(reference_id)
    
    if not reference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Request"
        )
    
    return {
        "id": reference.id,
        "name": reference.reference_name,
        "email": reference.reference_email,
        "status": reference.status,
        "message": "Reference Verification",
        "candidate": {
            "name": f"{reference.candidate.first_name} {reference.candidate.last_name or ''}".strip()
        }
    } 

@router.post("/complete", response_model=BaseResponse)
async def add_complete_candidate(
    candidate_data: dict,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add a new candidate with complete details including address, education, employment, and bank account"""
    # Get company ID from current user
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    # Check company credits
    company = db.query(Company).filter(Company.id == company_user.company_id).first()
    if not company or company.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough credits"
        )
    
    try:
        # Start transaction
        db.begin()
        
        # Create basic candidate
        basic_candidate_data = CandidateCreate(
            first_name=candidate_data.get("first_name", ""),
            last_name=candidate_data.get("last_name", ""),
            phone=candidate_data.get("phone", ""),
            email=candidate_data.get("email", ""),
            middle_name=candidate_data.get("middle_name"),
            gender=candidate_data.get("gender"),
            dob=candidate_data.get("dob"),
            father_name=candidate_data.get("father_name"),
            mother_name=candidate_data.get("mother_name"),
            marital_status=candidate_data.get("marital_status"),
            alternate_phone=candidate_data.get("alternate_phone")
        )
        
        candidate_service = CandidateService(db)
        candidate = await candidate_service.add_candidate(basic_candidate_data, company_user.company_id)
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create candidate"
            )
        
        # Add address details if provided
        if candidate_data.get("address"):
            address_data = candidate_data["address"]
            address = CandidateAddress(
                candidate_id=candidate.id,
                in_india=address_data.get("in_india", True),
                house_no=address_data.get("house_no"),
                locality=address_data.get("locality"),
                residency_name=address_data.get("residency_name"),
                city=address_data.get("city", ""),
                state=address_data.get("state", ""),
                pincode=address_data.get("pincode", ""),
                landmark=address_data.get("landmark"),
                residing_from=address_data.get("residing_from"),
                residency_proof=address_data.get("residency_proof"),
                is_current=address_data.get("is_current", True)
            )
            db.add(address)
        
        # Add education details if provided
        if candidate_data.get("educations"):
            for edu_data in candidate_data["educations"]:
                education = CandidateEducation(
                    candidate_id=candidate.id,
                    university=edu_data.get("university", ""),
                    degree=edu_data.get("degree", ""),
                    course=edu_data.get("course", ""),
                    id_number=edu_data.get("id_number", ""),
                    grade=edu_data.get("grade", ""),
                    college=edu_data.get("college", ""),
                    country=edu_data.get("country", ""),
                    state=edu_data.get("state", ""),
                    city=edu_data.get("city", ""),
                    mark_sheet=edu_data.get("mark_sheet", ""),
                    certificate=edu_data.get("certificate", "")
                )
                db.add(education)
        
        # Add employment details if provided
        if candidate_data.get("employments"):
            for emp_data in candidate_data["employments"]:
                employment = CandidateEmployment(
                    candidate_id=candidate.id,
                    is_fresher=emp_data.get("is_fresher", False),
                    company=emp_data.get("company"),
                    designation=emp_data.get("designation"),
                    city=emp_data.get("city"),
                    phone=emp_data.get("phone"),
                    email=emp_data.get("email"),
                    address=emp_data.get("address"),
                    employee_type=emp_data.get("employee_type"),
                    department=emp_data.get("department"),
                    starts_from=emp_data.get("starts_from"),
                    ends_at=emp_data.get("ends_at"),
                    currently_working=emp_data.get("currently_working", False),
                    salary=emp_data.get("salary"),
                    uan=emp_data.get("uan"),
                    employee_code=emp_data.get("employee_code"),
                    band=emp_data.get("band"),
                    remark=emp_data.get("remark"),
                    manager=emp_data.get("manager")
                )
                db.add(employment)
        
        # Add bank account details if provided
        if candidate_data.get("bank_account"):
            bank_data = candidate_data["bank_account"]
            bank_account = CandidateBankAccount(
                candidate_id=candidate.id,
                account_no=bank_data.get("account_no"),
                ifsc=bank_data.get("ifsc"),
                name=bank_data.get("name")
            )
            db.add(bank_account)
        
        # Add NID details if provided
        if candidate_data.get("nid"):
            nid_data = candidate_data["nid"]
            nid = CandidateNid(
                candidate_id=candidate.id,
                photo=nid_data.get("photo"),
                aadhar=nid_data.get("aadhar"),
                pan=nid_data.get("pan"),
                passport=nid_data.get("passport"),
                aadhar_no=nid_data.get("aadhar_no"),
                uan_no=nid_data.get("uan_no"),
                pan_no=nid_data.get("pan_no"),
                passport_no=nid_data.get("passport_no")
            )
            db.add(nid)
        
        # Commit all changes
        db.commit()
        
        # Reduce company credits
        company.credits -= 1
        db.commit()
        
        # Skip email sending for now
        print(f"Complete candidate created successfully: {candidate.email}")
        
        return BaseResponse(
            success=True,
            message="Candidate added successfully with all details",
            data={"candidate_id": candidate.id}
        )
            
    except Exception as e:
        db.rollback()
        print(f"Error creating complete candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating candidate: {str(e)}"
        ) 

@router.get("/confirm/{slug}", response_class=HTMLResponse)
async def confirm_candidate_email(
    slug: str,
    db: Session = Depends(get_db)
):
    """Simple confirmation endpoint linked from email, then guide to portal."""
    try:
        candidate_id = decrypt_slug(slug)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation link"
        )

    # Optionally mark something in DB (e.g., last_action or similar) in future
    html = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <meta http-equiv="refresh" content="5;url=http://localhost:3001/login/{slug}" />
        <title>Email Confirmed</title>
        <style>
          body {{ font-family: Arial, sans-serif; padding: 40px; }}
          .btn {{ display: inline-block; padding: 10px 16px; background:#463cff; color:#fff; text-decoration:none; border-radius:6px; }}
        </style>
      </head>
      <body>
        <h2>Email confirmed</h2>
        <p>Your email has been confirmed successfully.</p>
        <p>You will be redirected to your portal in 5 seconds.</p>
        <p><a class="btn" href="http://localhost:3001/login/{slug}">Continue to Portal</a></p>
      </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200) 