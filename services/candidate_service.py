# services/candidate_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from datetime import date as _date

from models.candidate import Candidate, CandidateNid, CandidateAddress, CandidateEducation, CandidateEmployment, CandidateBankAccount, CandidateAadharDetails, CheckStatus
from models.candidate import Gender as ModelGender
from models.verification import VerificationStatus, ReportIdentity, ReportEmployment, ReportCourtCheck, ReportAml, ReportBankAccount
from models.reference import CandidateReferenceCheck
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateLogin
from dependencies.auth import get_password_hash, create_access_token
from utils.candidate_utils import generate_candidate_code
import re
from models.company import Company


def camel_to_snake(name):
    """Convert camelCase or PascalCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class CandidateService:
    def __init__(self, db: Session):
        self.db = db

    async def add_candidate(self, candidate_data: CandidateCreate, company_id: int) -> Optional[Candidate]:
        """Add a new candidate"""
        try:
            # Generate candidate code
            candidate_code = generate_candidate_code()
            
            # Create candidate with all fields
            candidate = Candidate(
                candidate_code=candidate_code,
                first_name=candidate_data.first_name,
                middle_name=candidate_data.middle_name,
                last_name=candidate_data.last_name,
                gender=candidate_data.gender,
                dob=candidate_data.dob,
                father_name=candidate_data.father_name,
                mother_name=candidate_data.mother_name,
                marital_status=candidate_data.marital_status,
                phone=candidate_data.phone,
                alternate_phone=candidate_data.alternate_phone,
                email=candidate_data.email,
                company_id=company_id,
                score=100,  # Default score
                identity_check=CheckStatus.pending,
                employment_check=CheckStatus.pending,
                court_check=CheckStatus.pending,
                aml_check=CheckStatus.pending,
                bank_account_check=CheckStatus.pending
            )
            
            self.db.add(candidate)
            self.db.commit()
            self.db.refresh(candidate)
            
            # Load company relationship for email service
            candidate.company = self.db.query(Company).filter(Company.id == company_id).first()
            
            print(f"Created candidate with ID: {candidate.id}, DOB: {candidate.dob}")
            return candidate
            
        except Exception as e:
            self.db.rollback()
            print(f"Error creating candidate: {str(e)}")
            raise e

    async def add_candidates(self, candidates_data: List[CandidateCreate], company_id: int) -> List[Candidate]:
        """Add multiple candidates"""
        candidates = []
        for candidate_data in candidates_data:
            candidate = await self.add_candidate(candidate_data, company_id)
            if candidate:
                candidates.append(candidate)
        
        return candidates

    async def get_candidates(self, company_id: int, limit: int = 10, offset: int = 0) -> List[Candidate]:
        """Get candidates with pagination"""
        candidates = self.db.query(Candidate).filter(
            Candidate.company_id == company_id
        ).offset(offset).limit(limit).all()
        
        return candidates

    async def get_candidate_by_id(self, candidate_id: int) -> Optional[Candidate]:
        """Get candidate by ID"""
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()

    async def get_candidate_for_email(self, candidate_id: int) -> Optional[Candidate]:
        """Get candidate with company info for email"""
        return self.db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()

    async def approve_candidate(self, candidate_id: int) -> bool:
        """Approve candidate: set verification to COMPLETED, mark checks verified, ensure reports, compute score"""
        candidate = await self.get_candidate_by_id(candidate_id)
        if not candidate:
            return False

        # Ensure verification status COMPLETED exists
        completed_status = self.db.query(VerificationStatus).filter(VerificationStatus.name == "COMPLETED").first()
        if not completed_status:
            completed_status = VerificationStatus(name="COMPLETED")
            self.db.add(completed_status)
            self.db.flush()
        candidate.verification_status_id = completed_status.id

        # Mark all checks as verified
        candidate.identity_check = CheckStatus.verified
        candidate.employment_check = CheckStatus.verified
        candidate.court_check = CheckStatus.verified
        candidate.aml_check = CheckStatus.verified
        candidate.bank_account_check = CheckStatus.verified

        # Ensure report records exist and assign simple scores
        if not candidate.report_identity:
            ri = ReportIdentity(candidate_id=candidate.id, score=100)
            self.db.add(ri)
        else:
            candidate.report_identity.score = candidate.report_identity.score or 100

        if not candidate.report_employment:
            re = ReportEmployment(candidate_id=candidate.id)
            self.db.add(re)

        if not candidate.report_court_check:
            rc = ReportCourtCheck(candidate_id=candidate.id, score=100)
            self.db.add(rc)
        else:
            candidate.report_court_check.score = candidate.report_court_check.score or 100

        if not candidate.report_aml:
            ra = ReportAml(candidate_id=candidate.id, score=100)
            self.db.add(ra)
        else:
            candidate.report_aml.score = candidate.report_aml.score or 100

        if not candidate.report_bank_account:
            rb = ReportBankAccount(candidate_id=candidate.id, score=100)
            self.db.add(rb)
        else:
            candidate.report_bank_account.score = candidate.report_bank_account.score or 100

        # Compute overall score (simple average of available component scores)
        scores = [
            (candidate.report_identity.score if candidate.report_identity else 100),
            (candidate.report_court_check.score if candidate.report_court_check else 100),
            (candidate.report_aml.score if candidate.report_aml else 100),
            (candidate.report_bank_account.score if candidate.report_bank_account else 100),
        ]
        candidate.score = int(sum(scores) / len(scores)) if scores else 100

        candidate.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(candidate)
        return True

    async def update_candidate(self, candidate_data: CandidateUpdate, candidate_id: int) -> Optional[Candidate]:
        """Update candidate information"""
        candidate = await self.get_candidate_by_id(candidate_id)
        if not candidate:
            return None

        # Update basic fields
        update_data = candidate_data.dict(exclude_unset=True)
        basic_fields = ['first_name', 'middle_name', 'last_name', 'gender', 'dob',
                       'father_name', 'mother_name', 'marital_status', 'phone',
                       'alternate_phone', 'email']

        for field in basic_fields:
            if field in update_data and hasattr(candidate, field):
                setattr(candidate, field, update_data[field])

        # Handle nested data
        if 'meta' in update_data and update_data['meta']:
            # Update basic details from meta
            meta = update_data['meta']
            if 'firstName' in meta:
                candidate.first_name = meta['firstName']
            if 'lastName' in meta:
                candidate.last_name = meta['lastName']
            if 'middleName' in meta:
                candidate.middle_name = meta['middleName']
            if 'phone' in meta:
                candidate.phone = meta['phone']
            if 'email' in meta:
                candidate.email = meta['email']
            if 'alternatePhone' in meta:
                candidate.alternate_phone = meta['alternatePhone']
            if 'gender' in meta:
                g = meta['gender']
                if isinstance(g, str):
                    g_key = g.strip().lower()
                    mapping = {"male": "Male", "female": "Female", "others": "Others", "other": "Others"}
                    model_name = mapping.get(g_key)
                    if model_name and hasattr(ModelGender, model_name):
                        candidate.gender = getattr(ModelGender, model_name)
                    else:
                        candidate.gender = None
                elif isinstance(g, ModelGender):
                    candidate.gender = g
            if 'dob' in meta:
                dob_val = meta['dob']
                if isinstance(dob_val, str):
                    dob_val = dob_val.strip()
                    if dob_val:
                        try:
                            candidate.dob = datetime.strptime(dob_val, '%Y-%m-%d').date()
                        except Exception:
                            # Ignore parse errors and leave as None
                            candidate.dob = None
                    else:
                        candidate.dob = None
                elif isinstance(dob_val, _date):
                    candidate.dob = dob_val
            if 'fatherName' in meta:
                candidate.father_name = meta['fatherName']
            if 'motherName' in meta:
                candidate.mother_name = meta['motherName']
            if 'maritalStatus' in meta:
                candidate.marital_status = meta['maritalStatus']

        # Handle NID data
        if 'nid' in update_data and update_data['nid']:
            existing_nid = self.db.query(CandidateNid).filter_by(candidate_id=candidate.id).first()
            nid_data_raw = update_data['nid'].dict() if hasattr(update_data['nid'], "dict") else update_data['nid']
            nid_data = {
                'aadhar_no': nid_data_raw.get('aadharNo'),
                'pan_no': nid_data_raw.get('panNo'),
                'voter_id': nid_data_raw.get('voterId'),
                'passport_no': nid_data_raw.get('passportNo'),
            }
            nid_data = {k: v for k, v in nid_data.items() if v is not None}
            if existing_nid:
                for key, value in nid_data.items():
                    setattr(existing_nid, key, value)
            else:
                new_nid = CandidateNid(candidate_id=candidate.id, **nid_data)
                self.db.add(new_nid)

        # Handle bank account data
        if 'bankAccount' in update_data and update_data['bankAccount']:
            existing_bank = self.db.query(CandidateBankAccount).filter_by(candidate_id=candidate.id).first()
            bank_data_raw = update_data['bankAccount'].dict() if hasattr(update_data['bankAccount'], "dict") else \
            update_data['bankAccount']

            bank_data = {
                'account_no': bank_data_raw.get('accountNo'),
                'ifsc': bank_data_raw.get('ifsc'),
                'name': bank_data_raw.get('name')
            }
            bank_data = {k: v for k, v in bank_data.items() if v is not None}

            if existing_bank:
                for key, value in bank_data.items():
                    setattr(existing_bank, key, value)
            else:
                new_bank = CandidateBankAccount(candidate_id=candidate.id, **bank_data)
                self.db.add(new_bank)

        # Handle address data
        # Handle address data
        if 'address' in update_data and update_data['address']:
            self.db.query(CandidateAddress).filter_by(candidate_id=candidate.id).delete()
            address_list = update_data['address']

            for addr in address_list:
                address_raw = addr.dict() if hasattr(addr, "dict") else addr

                # Map frontend keys to model columns
                residing_from_val = address_raw.get('residingFrom')
                if isinstance(residing_from_val, str) and residing_from_val:
                    try:
                        residing_from_parsed = datetime.strptime(residing_from_val, '%Y-%m-%d').date()
                    except Exception:
                        residing_from_parsed = None
                else:
                    residing_from_parsed = None

                address_data = {
                    'in_india': address_raw.get('inIndia'),
                    'house_no': address_raw.get('houseNo'),
                    'locality': address_raw.get('locality'),
                    'residency_name': address_raw.get('residencyName'),
                    'city': address_raw.get('city'),
                    'state': address_raw.get('state'),
                    'pincode': address_raw.get('pincode'),
                    'landmark': address_raw.get('landmark'),
                    'residing_from': residing_from_parsed,
                    'residency_proof': address_raw.get('residencyProof'),
                    'is_current': address_raw.get('isCurrent'),
                }

                # Remove any None values
                address_data = {k: v for k, v in address_data.items() if v is not None}

                new_address = CandidateAddress(candidate_id=candidate.id, **address_data)
                self.db.add(new_address)

        # Handle education data
        if 'education' in update_data and update_data['education']:
            education_list = update_data['education']
            self.db.query(CandidateEducation).filter_by(candidate_id=candidate.id).delete()

            for edu in education_list:
                education_data = edu.dict() if hasattr(edu, "dict") else edu

                # Map camelCase or different keys to model keys
                key_map = {
                    "idNumber": "id_number",
                    "certificateNumber": "certificate",
                    "markSheet": "mark_sheet",
                    # add other mappings if needed
                }

                for old_key, new_key in key_map.items():
                    if old_key in education_data:
                        education_data[new_key] = education_data.pop(old_key)

                # Filter keys allowed by CandidateEducation model
                allowed_keys = {
                    "university", "degree", "course", "id_number", "grade",
                    "college", "country", "state", "city", "mark_sheet", "certificate"
                }

                filtered_data = {k: v for k, v in education_data.items() if k in allowed_keys}

                new_education = CandidateEducation(candidate_id=candidate.id, **filtered_data)
                self.db.add(new_education)

        # Allowed keys for CandidateEmployment model fields
        allowed_keys = {
            "is_fresher",
            "company",
            "designation",
            "city",
            "phone",
            "email",
            "address",
            "employee_type",
            "department",
            "starts_from",
            "ends_at",
            "currently_working",
            "salary",
            "uan",
            "employee_code",
            "band",
            "remark",
            "manager"
        }

        if 'employment' in update_data and update_data['employment']:
            employment_data_block = update_data['employment']

            # If `employment` is a dict and has a `data` key, use it
            if isinstance(employment_data_block, dict) and 'data' in employment_data_block:
                employment_list = employment_data_block['data']
            elif isinstance(employment_data_block, list):
                employment_list = employment_data_block
            else:
                employment_list = []

            # Delete old records
            self.db.query(CandidateEmployment).filter_by(candidate_id=candidate.id).delete()

            for emp in employment_list:
                if hasattr(emp, "dict"):
                    employment_data = emp.dict(by_alias=False)
                elif isinstance(emp, dict):
                    employment_data = emp
                else:
                    print(f"Skipping invalid employment entry: {emp} (type: {type(emp)})")
                    continue

                # Convert camelCase keys to snake_case
                employment_data_snake = {
                    camel_to_snake(k): v for k, v in employment_data.items()
                    if camel_to_snake(k) in allowed_keys and not isinstance(v, dict)
                }

                new_employment = CandidateEmployment(candidate_id=candidate.id, **employment_data_snake)
                self.db.add(new_employment)

        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    async def update_candidate_status(self, status: str, candidate_id: int) -> bool:
        """Update candidate verification status"""
        candidate = await self.get_candidate_by_id(candidate_id)
        if not candidate:
            return False
        
        # Get verification status
        verification_status = self.db.query(VerificationStatus).filter(
            VerificationStatus.name == status
        ).first()
        
        if verification_status:
            candidate.verification_status_id = verification_status.id
        
        self.db.commit()
        return True

    async def candidate_login(self, login_data: CandidateLogin) -> Dict[str, Any]:
        """Candidate login"""
        email_normalized = (login_data.email or "").strip().lower()

        candidate: Optional[Candidate] = None
        # If id is provided (from slug), validate that the email matches that candidate
        if getattr(login_data, "id", None):
            candidate = self.db.query(Candidate).filter(Candidate.id == login_data.id).first()
            if not candidate or (candidate.email or "").strip().lower() != email_normalized:
                raise ValueError("Invalid credentials")
        else:
            candidate = self.db.query(Candidate).filter(
                Candidate.email == email_normalized
            ).first()
        
        if not candidate:
            raise ValueError("Invalid credentials")
        
        # For candidates without password, allow login with email only
        if not candidate.password:
            # Generate access token for email-only login
            access_token = create_access_token(
                data={"sub": str(candidate.id), "email": candidate.email}
            )
            
            return {
                "accessToken": access_token,
                "token_type": "bearer",
                "id": candidate.id,
                "email": candidate.email,
                "firstName": candidate.first_name or "",
                "lastName": candidate.last_name or "",
                "phone": candidate.phone or "",
                "image": candidate.image,
                "company": {
                    "id": candidate.company.id if candidate.company else 0,
                    "name": candidate.company.name if candidate.company else "",
                    "logo": candidate.company.logo if candidate.company else None
                }
            }
        
        # Verify password if password exists
        if candidate.password != login_data.password:
            raise ValueError("Invalid credentials")
        
        # Generate access token
        access_token = create_access_token(
            data={"sub": str(candidate.id), "email": candidate.email}
        )
        
        return {
            "accessToken": access_token,
            "token_type": "bearer",
            "id": candidate.id,
            "email": candidate.email,
            "firstName": candidate.first_name or "",
            "lastName": candidate.last_name or "",
            "phone": candidate.phone or "",
            "image": candidate.image,
            "company": {
                "id": candidate.company.id if candidate.company else 0,
                "name": candidate.company.name if candidate.company else "",
                "logo": candidate.company.logo if candidate.company else None
            }
        }

    async def get_candidate_insights(self, company_id: int) -> Dict[str, Any]:
        """Get candidate insights for company"""
        total_candidates = self.db.query(Candidate).filter(
            Candidate.company_id == company_id
        ).count()
        
        pending_candidates = self.db.query(Candidate).filter(
            and_(
                Candidate.company_id == company_id,
                or_(
                    Candidate.verification_status_id.is_(None),
                    VerificationStatus.name == "PENDING"
                )
            )
        ).count()
        
        completed_candidates = self.db.query(Candidate).filter(
            and_(
                Candidate.company_id == company_id,
                VerificationStatus.name == "COMPLETED"
            )
        ).count()
        
        return {
            "total": total_candidates,
            "pending": pending_candidates,
            "completed": completed_candidates
        }

    async def reject_candidate(self, candidate_id: int) -> bool:
        """Reject candidate"""
        candidate = await self.get_candidate_by_id(candidate_id)
        if not candidate:
            return False
        
        # Update status to rejected
        await self.update_candidate_status("REJECTED", candidate_id)
        return True

    async def update_aadhar_details(self, aadhar_data: Dict[str, Any], candidate_id: int) -> bool:
        """Update Aadhar details"""
        candidate = await self.get_candidate_by_id(candidate_id)
        if not candidate:
            return False
        
        # Create or update Aadhar details
        aadhar_details = self.db.query(CandidateAadharDetails).filter(
            CandidateAadharDetails.candidate_id == candidate_id
        ).first()
        
        if not aadhar_details:
            aadhar_details = CandidateAadharDetails(candidate_id=candidate_id)
            self.db.add(aadhar_details)
        
        # Update fields
        for field, value in aadhar_data.items():
            if hasattr(aadhar_details, field):
                setattr(aadhar_details, field, value)
        
        self.db.commit()
        return True

    async def get_reference_data(self, company_id: int) -> List[CandidateReferenceCheck]:
        """Get reference data for company"""
        return self.db.query(CandidateReferenceCheck).filter(
            CandidateReferenceCheck.company_id == company_id
        ).all()

    async def reference_login(self, reference_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reference login"""
        reference = self.db.query(CandidateReferenceCheck).filter(
            CandidateReferenceCheck.id == reference_data.get("reference_id")
        ).first()
        
        if not reference:
            raise ValueError("Invalid reference")
        
        # Generate access token
        access_token = create_access_token(
            data={"sub": str(reference.id), "type": "reference"}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "reference_id": reference.id,
            "name": reference.reference_name,
            "email": reference.reference_email
        }

    async def update_reference(self, reference_data: Dict[str, Any]) -> bool:
        """Update reference information"""
        reference = self.db.query(CandidateReferenceCheck).filter(
            CandidateReferenceCheck.id == reference_data.get("reference_id")
        ).first()
        
        if not reference:
            return False
        
        # Update fields
        for field, value in reference_data.items():
            if hasattr(reference, field) and field != "reference_id":
                setattr(reference, field, value)
        
        self.db.commit()
        return True

    async def get_reference(self, reference_id: int) -> Optional[CandidateReferenceCheck]:
        """Get reference by ID"""
        return self.db.query(CandidateReferenceCheck).filter(
            CandidateReferenceCheck.id == reference_id
        ).first() 