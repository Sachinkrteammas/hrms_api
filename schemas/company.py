from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CompanyCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    logo: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    gst: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    residency_no: Optional[str] = Field(None, max_length=20)
    landmark: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    logo: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    gst: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    residency_no: Optional[str] = Field(None, max_length=20)
    landmark: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

class CompanyResponse(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    gst: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    residency_no: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    credits: int
    created_at: datetime

    class Config:
        from_attributes = True
