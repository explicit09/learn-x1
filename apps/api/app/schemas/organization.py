from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class OrganizationBase(BaseModel):
    """Base organization schema with common fields."""
    name: str
    domain: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    """Organization creation schema."""
    pass

class OrganizationUpdate(BaseModel):
    """Organization update schema."""
    name: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None

class Organization(OrganizationBase):
    """Organization response schema."""
    id: str
    is_active: bool = True
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class OrganizationWithStats(Organization):
    """Organization with additional statistics."""
    user_count: int
    course_count: int
    
    class Config:
        from_attributes = True
