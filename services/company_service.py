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

    async def upsert_company(self, company_id: Optional[int], admin_id: int, company_data: Optional[Dict] = None, credits: Optional[int] = None, subscription_id: int = 1) -> Company:
        """Create or update company for super admin"""
        if company_id:
            # Update existing company
            company = await self.get_company_by_id(company_id)
            if not company:
                raise ValueError("Company not found")
        else:
            # Create new company with generated code
            import random
            import string
            
            # Generate unique company code
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                existing_company = self.db.query(Company).filter(Company.code == code).first()
                if not existing_company:
                    break
            
            company = Company(
                code=code,
                name=f"Company_{code}",
                credits=credits or 0
            )
            self.db.add(company)
            self.db.flush()

        # Update company fields
        if company_data:
            for field, value in company_data.items():
                if hasattr(company, field):
                    setattr(company, field, value)

        if credits is not None:
            company.credits = credits

        # Create subscription company relationship if needed
        from models.company import SubscriptionCompany, Subscription
        existing_subscription = self.db.query(SubscriptionCompany).filter(
            SubscriptionCompany.company_id == company.id
        ).first()
        
        if not existing_subscription:
            # Check if subscription exists, create if not
            subscription = self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not subscription:
                subscription = Subscription(
                    id=subscription_id,
                    name="Basic",
                    services=[]
                )
                self.db.add(subscription)
                self.db.flush()
            
            subscription_company = SubscriptionCompany(
                company_id=company.id,
                subscription_id=subscription_id
            )
            self.db.add(subscription_company)

        self.db.commit()
        self.db.refresh(company)
        
        # Create company user relationship for super admin
        from models.user import CompanyUser
        existing_company_user = self.db.query(CompanyUser).filter(
            CompanyUser.user_id == admin_id
        ).first()
        
        if not existing_company_user:
            company_user = CompanyUser(
                company_id=company.id,
                user_id=admin_id
            )
            self.db.add(company_user)
            self.db.commit()
        
        return company

    async def get_company_subscription_and_services(self, company_id: int) -> Dict[str, Any]:
        """Get company subscription and services"""
        company = await self.get_company_by_id(company_id)
        if not company:
            return {"subscription": None, "services": []}

        subscription = None
        services = []
        
        # Get subscription details if available
        if hasattr(company, 'subscription_company') and company.subscription_company:
            subscription = company.subscription_company.subscription
            if hasattr(subscription, 'services'):
                services = subscription.services

        return {
            "subscription": subscription,
            "services": services
        }
