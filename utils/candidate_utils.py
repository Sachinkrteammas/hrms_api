import uuid
import base64
import hashlib
from typing import Dict, Any

def generate_candidate_code() -> str:
    """Generate unique candidate code"""
    return str(uuid.uuid4())

def encrypt_slug(id_str: str) -> str:
    """Encrypt ID to create slug"""
    # Simple base64 encoding for now
    # In production, use proper encryption
    encoded = base64.b64encode(id_str.encode()).decode()
    return encoded.replace('+', '-').replace('/', '_').replace('=', '')

def decrypt_slug(slug: str) -> int:
    """Decrypt slug to get ID"""
    try:
        # Reverse the encoding
        slug = slug.replace('-', '+').replace('_', '/')
        # Add padding if needed
        while len(slug) % 4:
            slug += '='
        
        decoded = base64.b64decode(slug).decode()
        return int(decoded)
    except:
        raise ValueError("Invalid slug")

def get_candidate_name(candidate) -> str:
    """Get candidate full name"""
    if not candidate:
        return ""
    
    name_parts = [candidate.first_name or ""]
    if candidate.middle_name:
        name_parts.append(candidate.middle_name)
    if candidate.last_name:
        name_parts.append(candidate.last_name)
    
    return " ".join(name_parts).strip()

def get_candidate_status_for_candidate(status: str) -> str:
    """Get candidate-friendly status"""
    status_mapping = {
        "PENDING": "Pending",
        "REQUESTED": "Requested",
        "IN_PROGRESS": "In Progress",
        "SUBMITTED": "Submitted",
        "COMPLETED": "Completed",
        "REJECTED": "Rejected"
    }
    return status_mapping.get(status, "Pending")

def get_candidate_login_data(candidate) -> Dict[str, Any]:
    """Get candidate login data"""
    return {
        "candidate_id": candidate.id,
        "email": candidate.email,
        "name": get_candidate_name(candidate),
        "access_token": candidate.access_token
    }

def get_candidate_message(candidate) -> str:
    """Generate candidate email message"""
    return f"""
    Welcome to our background verification process
    
    Dear {candidate.first_name},
    
    You have been invited to complete your background verification for {candidate.company.name if candidate.company else 'our company'}.
    
    Please visit the following link to access your verification portal:
    {candidate.candidate_code}
    
    Best regards,
    HR Team
    """

def get_reference_verification_message(candidate, reference_data: Dict[str, Any]) -> str:
    """Generate reference verification email message"""
    return f"""
    Reference Check Request
    
    Dear {reference_data['name']},
    
    We are conducting a background verification for {get_candidate_name(candidate)} and would appreciate your reference.
    
    Please provide your feedback by visiting the following link:
    {reference_data['id']}
    
    Thank you for your cooperation.
    
    Best regards,
    HR Team
    """

def get_aml_dto(candidate) -> Dict[str, Any]:
    """Get AML verification DTO"""
    return {
        "name": get_candidate_name(candidate),
        "phone": candidate.phone,
        "email": candidate.email,
        "address": candidate.aadhar_address
    }

def get_bank_account_dto(candidate) -> Dict[str, Any]:
    """Get bank account verification DTO"""
    if not candidate.bank_account:
        return None
    
    return {
        "account_number": candidate.bank_account.account_no,
        "ifsc_code": candidate.bank_account.ifsc,
        "account_holder_name": candidate.bank_account.name
    }

def get_employment_dto(candidate) -> Dict[str, Any]:
    """Get employment verification DTO"""
    if not candidate.employments:
        return {"isFresher": True}
    
    employment = candidate.employments[0]  # Get first employment
    return {
        "isFresher": employment.is_fresher or False,
        "uan": candidate.uan,
        "company": employment.company,
        "designation": employment.designation
    }

def get_court_check_dto(candidate) -> Dict[str, Any]:
    """Get court check DTO"""
    return {
        "name": get_candidate_name(candidate),
        "phone": candidate.phone,
        "email": candidate.email,
        "address": candidate.aadhar_address
    } 