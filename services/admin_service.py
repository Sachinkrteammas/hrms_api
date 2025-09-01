# services/admin_service.py
from sqlalchemy.orm import Session
from models.user import User, Role
from models.company import Company
from schemas.admin import WhiteListSuperAdminDTO, WhiteListAdminDTO
from fastapi import HTTPException, status
import random
import string

class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def generate_pass_code(self) -> str:
        """Generate a 6-digit pass code"""
        return ''.join(random.choices(string.digits, k=6))

    def get_admin_sign_up_message(self, pass_code: str) -> str:
        """Generate admin sign up message"""
        return f"Please signup to our portal using the following link: http://hr.theinfiniti.ai/sign-up\nUse {pass_code} as your one time pass code"

    async def white_list_super_admin(self, dto: WhiteListSuperAdminDTO) -> User:
        """Create a super admin user"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == dto.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )

        # Get super admin role
        super_admin_role = self.db.query(Role).filter(Role.name == "SUPERADMIN").first()
        if not super_admin_role:
            # Create super admin role if it doesn't exist
            super_admin_role = Role(name="SUPERADMIN")
            self.db.add(super_admin_role)
            self.db.flush()

        # Generate pass code
        pass_code = self.generate_pass_code()

        # Create user
        user = User(
            email=dto.email,
            role=super_admin_role.id,
            pass_code=pass_code
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)

        return user

    async def white_list_admin(self, dto: WhiteListAdminDTO, company_id: int) -> User:
        """Create an admin user for a specific company"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == dto.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )

        # Get role
        role = self.db.query(Role).filter(Role.name == dto.role).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not found"
            )

        # Generate pass code
        pass_code = self.generate_pass_code()

        # Create user
        user = User(
            email=dto.email,
            role=role.id,
            pass_code=pass_code
        )
        self.db.add(user)
        self.db.flush()

        # Create company user relationship
        from models.user import CompanyUser
        company_user = CompanyUser(
            company_id=company_id,
            user_id=user.id
        )
        self.db.add(company_user)
        self.db.flush()
        self.db.refresh(user)

        return user

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    async def get_admin_pass_code(self, admin_id: int) -> User:
        """Get admin pass code for email resend"""
        admin = self.db.query(User).filter(
            User.id == admin_id,
            User.is_shadowed == False
        ).first()

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not exist"
            )

        if admin.meta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already signed up"
            )

        return admin

    async def delete_admin(self, admin_id: int) -> bool:
        """Delete admin user"""
        admin = self.db.query(User).filter(User.id == admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        # Soft delete by setting is_shadowed to True
        admin.is_shadowed = True
        self.db.commit()
        return True

    async def reset_password(self, user_id: int, new_password: str) -> bool:
        """Reset user password"""
        from dependencies.auth import get_password_hash
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        user.password = get_password_hash(new_password)
        self.db.commit()
        return True
