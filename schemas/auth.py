from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserSignUp(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1, max_length=100)
    company_code: str = Field(..., min_length=1, max_length=20)
    pass_code: str = Field(..., min_length=6, max_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OtpRequest(BaseModel):
    email: EmailStr

class OtpVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class TokenResponse(BaseModel):
    accessToken: str
    token_type: str = "bearer"
    id: int
    email: str
    firstName: str
    lastName: str
    phone: str
    image: Optional[str] = None
    company: dict

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    company_id: Optional[int] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True 