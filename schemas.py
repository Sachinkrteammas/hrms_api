from typing import Optional

from pydantic import BaseModel, EmailStr

class UserSignUpDTO(BaseModel):
    email: EmailStr
    password: str
    pass_code: str
    name: str


class UserLogInDTO(BaseModel):
    email: EmailStr
    password: str


class CandidateDTO(BaseModel):
    name: str
    # other fields...

class CandidateUpdateDTO(BaseModel):
    name: Optional[str]
    verify: Optional[bool] = False

class PaginationQueryParams(BaseModel):
    limit: int = 10
    next: int = 0
