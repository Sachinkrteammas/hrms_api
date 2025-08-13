# services/company_service.py
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from models.company import Company
from schemas.company import CompanyUpdate

class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    async def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """Get company by ID"""
        return self.db.query(Company).filter(Company.id == company_id).first()

    async def get_company_by_code(self, company_code: str) -> Optional[Company]:
        """Get company by code"""
        return self.db.query(Company).filter(Company.code == company_code).first()

    async def update_company(self, company_data: CompanyUpdate, company_id: int) -> Optional[Company]:
        """Update company information"""
        company = await self.get_company_by_id(company_id)
        if not company:
            return None
        
        # Update fields
        update_data = company_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(company, field):
                setattr(company, field, value)
        
        self.db.commit()
        self.db.refresh(company)
        
        return company

    async def get_credits(self, company_id: int) -> int:
        """Get company credits"""
        company = await self.get_company_by_id(company_id)
        return company.credits if company else 0

    async def add_credits(self, company_id: int, credits: int) -> bool:
        """Add credits to company"""
        company = await self.get_company_by_id(company_id)
        if not company:
            return False
        
        company.credits += credits
        self.db.commit()
        return True

    async def reduce_credits(self, company_id: int, credits: int) -> bool:
        """Reduce company credits"""
        company = await self.get_company_by_id(company_id)
        if not company or company.credits < credits:
            return False
        
        company.credits -= credits
        self.db.commit()
        return True
