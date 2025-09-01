from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import random

from models.database import get_db
from models.user import User, UserMeta, UserOtp, Role, CompanyUser
from models.company import Company
from schemas.auth import UserSignUp, UserLogin, OtpRequest, OtpVerify, TokenResponse, UserResponse
from dependencies.auth import (
    verify_password, get_password_hash, create_access_token, 
    generate_access_token, get_current_user
)
from services.email_service import EmailService
from services.candidate_service import CandidateService
from utils.candidate_utils import decrypt_slug

router = APIRouter()
security = HTTPBearer()

@router.post("/signup", response_model=TokenResponse)
async def user_signup(
    user_data: UserSignUp,
    db: Session = Depends(get_db)
):
    """User signup endpoint"""
    # Handle pass code - check both pass_code and passCode fields
    actual_pass_code = user_data.pass_code or user_data.passCode
    if not actual_pass_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pass code is required"
        )
    
    # Find user by pass code (for super admin signup)
    user_with_pass_code = db.query(User).filter(
        User.pass_code == actual_pass_code.strip(),
        User.email == user_data.email
    ).first()
    
    if not user_with_pass_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pass code or email combination"
        )
    
    # Check if user is already signed up (has password)
    if user_with_pass_code.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already signed up"
        )
    
    # Get user's role
    user_role = db.query(Role).filter(Role.id == user_with_pass_code.role).first()
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User role not found"
        )
    
    # Update user with password and clear pass code
    user_with_pass_code.password = get_password_hash(user_data.password)
    user_with_pass_code.pass_code = None  # Clear pass code after successful signup
    
    # Create user meta if not exists
    existing_meta = db.query(UserMeta).filter(UserMeta.user_id == user_with_pass_code.id).first()
    if not existing_meta:
        user_meta = UserMeta(
            name=user_data.name,
            user_id=user_with_pass_code.id
        )
        db.add(user_meta)
    
    # For super admin, find their company
    company = None
    if user_role.name == "SUPERADMIN":
        # Find company associated with super admin
        company_user = db.query(CompanyUser).filter(CompanyUser.user_id == user_with_pass_code.id).first()
        if company_user:
            company = db.query(Company).filter(Company.id == company_user.company_id).first()
    else:
        # For regular users, check company code
        if not user_data.company_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company code is required for non-super admin users"
            )
        company = db.query(Company).filter(Company.code == user_data.company_code).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company code"
            )
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company not found"
        )
    
    db.commit()
    db.refresh(user_with_pass_code)
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": str(user_with_pass_code.id), "email": user_with_pass_code.email}
    )
    
    return TokenResponse(
        accessToken=access_token,
        id=user_with_pass_code.id,
        email=user_with_pass_code.email,
        firstName=user_data.name.split()[0] if user_data.name else "",
        lastName=" ".join(user_data.name.split()[1:]) if user_data.name and len(user_data.name.split()) > 1 else "",
        phone="",
        company={
            "id": company.id,
            "name": company.name,
            "code": company.code
        }
    )

# @router.post("/login", response_model=TokenResponse)
# async def user_login(
#     user_data: UserLogin,
#     db: Session = Depends(get_db)
# ):
#     """User login endpoint"""
#     user = db.query(User).filter(User.email == user_data.email).first()
#     if not user or not verify_password(user_data.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password"
#         )
#
#     # Get user meta and company info
#     user_meta = db.query(UserMeta).filter(UserMeta.user_id == user.id).first()
#     company_user = db.query(CompanyUser).filter(CompanyUser.user_id == user.id).first()
#     role = db.query(Role).filter(Role.id == user.role).first()
#
#     # Generate access token
#     access_token = create_access_token(
#         data={"sub": str(user.id), "email": user.email}
#     )
#
#     return TokenResponse(
#         access_token=access_token,
#         user_id=user.id,
#         email=user.email,
#         name=user_meta.name if user_meta else "",
#         company_id=company_user.company_id if company_user else None,
#         role=role.name if role else ""
#     )

@router.post("/login", response_model=TokenResponse)
async def user_login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Get user meta and company info
    user_meta = db.query(UserMeta).filter(UserMeta.user_id == user.id).first()
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == user.id).first()
    company = (
        db.query(Company).filter(Company.id == company_user.company_id).first()
        if company_user else None
    )

    # Generate access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    # Parse name
    first_name = ""
    last_name = ""
    if user_meta and user_meta.name:
        name_parts = user_meta.name.strip().split(" ")
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    return TokenResponse(
        accessToken=access_token,
        token_type="bearer",
        id=user.id,
        email=user.email,
        firstName=first_name,
        lastName=last_name,
        phone=user_meta.phone if user_meta and hasattr(user_meta, "phone") else "",
        image=getattr(user_meta, "image", None),
        company={
            "id": company.id,
            "name": company.name
        } if company else {}
    )



@router.post("/otp/request")
async def request_otp(
    otp_data: OtpRequest,
    db: Session = Depends(get_db)
):
    """Request OTP endpoint"""
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    
    # Check if OTP already exists for this email
    existing_otp = db.query(UserOtp).filter(UserOtp.email == otp_data.email).first()
    if existing_otp:
        existing_otp.otp = otp
        existing_otp.updated_at = datetime.utcnow()
    else:
        new_otp = UserOtp(
            email=otp_data.email,
            otp=otp
        )
        db.add(new_otp)
    
    db.commit()
    
    # TODO: Send email with OTP
    # For now, just return success message
    return {"message": "OTP sent successfully"}

@router.post("/otp/verify", response_model=UserResponse)
async def verify_otp(
    otp_data: OtpVerify,
    db: Session = Depends(get_db)
):
    """Verify OTP endpoint"""
    # Find OTP record
    otp_record = db.query(UserOtp).filter(UserOtp.email == otp_data.email).first()
    if not otp_record or otp_record.otp != otp_data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Get user
    user = db.query(User).filter(User.email == otp_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Delete OTP record
    db.delete(otp_record)
    db.commit()
    
    # Get user meta and role
    user_meta = db.query(UserMeta).filter(UserMeta.user_id == user.id).first()
    role = db.query(Role).filter(Role.id == user.role).first()
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user_meta.name if user_meta else "",
        company_id=None,  # Will be set by frontend
        role=role.name if role else "",
        created_at=user.created_at
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    user_meta = db.query(UserMeta).filter(UserMeta.user_id == current_user.id).first()
    role = db.query(Role).filter(Role.id == current_user.role).first()
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=user_meta.name if user_meta else "",
        company_id=company_user.company_id if company_user else None,
        role=role.name if role else "",
        created_at=current_user.created_at
    ) 

@router.post("/candidate/loginBySlug")
async def candidate_login_by_slug(payload: dict, db: Session = Depends(get_db)):
    try:
        slug = payload.get("slug", "")
        email = payload.get("email", "")
        if not slug or not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing slug or email")
        candidate_id = decrypt_slug(slug)
        service = CandidateService(db)
        return await service.candidate_login(type("LoginData", (), {"email": email, "password": None, "id": candidate_id}))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") 