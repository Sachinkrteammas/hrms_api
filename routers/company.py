from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.user import User, CompanyUser
from models.company import Company
from schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from schemas.common import BaseResponse
from dependencies.auth import get_current_admin_user
from services.company_service import CompanyService

router = APIRouter()

@router.get("/profile", response_model=CompanyResponse)
async def get_company_profile(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get company profile for current user"""
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    company = db.query(Company).filter(Company.id == company_user.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company

@router.put("/profile", response_model=CompanyResponse)
async def update_company_profile(
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update company profile"""
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    company_service = CompanyService(db)
    updated_company = await company_service.update_company(company_data, company_user.company_id)
    
    return updated_company

@router.get("/credits")
async def get_company_credits(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get company credits"""
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    company_service = CompanyService(db)
    credits = await company_service.get_credits(company_user.company_id)
    
    return {"credits": credits}

@router.post("/credits/add")
async def add_company_credits(
    credits_data: dict,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add credits to company"""
    company_user = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).first()
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any company"
        )
    
    company_service = CompanyService(db)
    await company_service.add_credits(company_user.company_id, credits_data["credits"])
    
    return BaseResponse(message="Credits added successfully") 