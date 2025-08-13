from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar

T = TypeVar('T')

class BaseResponse(BaseModel):
    message: str
    success: bool = True
    slug: Optional[str] = None

class PaginationParams(BaseModel):
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    next: Optional[int] = Field(default=0, ge=0)

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    next: int
    total: Optional[int] = None

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None 