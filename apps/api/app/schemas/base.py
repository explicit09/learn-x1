from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

# Define a TypeVar for generic response models
T = TypeVar('T')

class BaseResponse(BaseModel):
    """Base response model with success status."""
    success: bool = True
    message: Optional[str] = None

class PaginatedResponseMeta(BaseModel):
    """Metadata for paginated responses."""
    page: int
    per_page: int
    total: int
    pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    success: bool = True
    message: Optional[str] = None
    data: List[T]
    meta: PaginatedResponseMeta

class DataResponse(BaseModel, Generic[T]):
    """Generic data response model."""
    success: bool = True
    message: Optional[str] = None
    data: T

class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = False
    error_code: Optional[str] = None
    detail: Optional[str] = None
