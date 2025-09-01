from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class WhiteListSuperAdminDTO(BaseModel):
    email: EmailStr
    credits: Optional[int] = None
    subscription_id: Optional[int] = Field(default=1, alias="subscriptionId")

class WhiteListAdminDTO(BaseModel):
    email: EmailStr
    role: str

class DeleteAdminDTO(BaseModel):
    id: int

class ResetPasswordDTO(BaseModel):
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Password must contain at least one special character (@$!%*?&)')
        return v

class EmailPassCodeDTO(BaseModel):
    id: int

class AdminResponse(BaseModel):
    message: str
    pass_code: Optional[str] = None  # For testing purposes
