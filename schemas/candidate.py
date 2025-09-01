from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
# Pydantic v2 config utilities
try:
    from pydantic import ConfigDict
except ImportError:  # fallback if older pydantic is used
    ConfigDict = dict  # type: ignore

class Gender(str, Enum):
    Male = "Male"
    Female = "Female"
    Others = "Others"

class CheckStatus(str, Enum):
    pending = "pending"
    api_failed = "api_failed"
    failed = "failed"
    verified = "verified"
    in_progress = "in_progress"

class ReferenceCheckStatus(str, Enum):
    PENDING = "PENDING"
    REQUESTED = "REQUESTED"
    SUBMITTED = "SUBMITTED"

class CandidateCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field("", max_length=100)
    last_name: Optional[str] = Field("", max_length=100)
    gender: Optional[Gender] = None
    dob: Optional[date] = None
    father_name: Optional[str] = Field("", max_length=100)
    mother_name: Optional[str] = Field("", max_length=100)
    marital_status: Optional[str] = Field("", max_length=50)
    phone: str = Field(..., min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field("", max_length=20)
    email: str = Field(..., min_length=1)

class ManagerInfo(BaseModel):
    firstName: Optional[str] = None
    middleName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    employeeCode: Optional[str] = None
    department: Optional[str] = None

class EmploymentUpdate(BaseModel):
    company: Optional[str]
    employeeCode: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    employeeType: Optional[str]
    manager: Optional[ManagerInfo]
    band: Optional[str]
    salary: Optional[int]
    startsFrom: Optional[date]
    currentlyWorking: Optional[bool]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    city: Optional[str]
    remark: Optional[str]

# ✅ Wrapper model to accept { employment: { data: [...] } }
class EmploymentWrapper(BaseModel):
    data: List[EmploymentUpdate]


class CandidateUpdate(BaseModel):
    # Accept both snake_case (default) and camelCase (via validation_alias)
    first_name: Optional[str] = Field(
        "",
        min_length=1,
        max_length=100,
        validation_alias="firstName",
    )
    middle_name: Optional[str] = Field(
        "",
        max_length=100,
        validation_alias="middleName",
    )
    last_name: Optional[str] = Field(
        "",
        max_length=100,
        validation_alias="lastName",
    )
    gender: Optional[Gender] = None
    dob: Optional[date] = None
    father_name: Optional[str] = Field(
        "",
        max_length=100,
        validation_alias="fatherName",
    )
    mother_name: Optional[str] = Field(
        "",
        max_length=100,
        validation_alias="motherName",
    )
    marital_status: Optional[str] = Field(
        "",
        max_length=50,
        validation_alias="maritalStatus",
    )
    phone: Optional[str] = Field("", min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field(
        "",
        max_length=20,
        validation_alias="alternatePhone",
    )
    email: Optional[str] = Field("", min_length=1)
    verify: Optional[bool] = False
    meta: Optional[dict] = None
    nid: Optional[dict] = None
    bankAccount: Optional[dict] = None
    address: Optional[list] = None
    education: Optional[list] = None
    employment: Optional[EmploymentWrapper] = None

    # Pydantic v2 model config to allow population by field name
    # and keep compatibility if imported in environments with pydantic<2
    model_config = ConfigDict(populate_by_name=True) if ConfigDict is not dict else None

class CandidateLogin(BaseModel):
    email: str = Field(..., min_length=1)
    password: Optional[str] = None
    id: Optional[int] = None

class CandidateResponse(BaseModel):
    id: int
    candidate_code: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    dob: Optional[date] = None
    phone: str
    email: str
    status: Optional[str] = None
    score: Optional[int] = None
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CandidateListResponse(BaseModel):
    items: List[CandidateResponse]
    insights: dict
    next: int

class ReferenceCreate(BaseModel):
    reference_name: str = Field(..., min_length=1, max_length=100)
    reference_email: str = Field(..., min_length=1)

class ReferenceUpdate(BaseModel):
    reference_name: Optional[str] = Field("", min_length=1, max_length=100)
    reference_email: Optional[str] = Field("", min_length=1)
    data: Optional[str] = None

class ReferenceResponse(BaseModel):
    id: int
    reference_name: str
    reference_email: str
    status: ReferenceCheckStatus
    candidate_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CandidateSendEmail(BaseModel):
    id: int

class CandidateReject(BaseModel):
    id: int

class CandidateAadharOTP(BaseModel):
    aadharNo: str = Field(..., min_length=12, max_length=12)

class CandidateAadharVerify(BaseModel):
    aadharNo: str = Field(..., min_length=12, max_length=12)
    otp: str = Field(..., min_length=6, max_length=6)
    referenceId: str = Field(..., min_length=1) 