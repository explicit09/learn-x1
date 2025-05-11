from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration."""
    STUDENT = "student"
    PROFESSOR = "professor"
    ADMIN = "admin"

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str
    role: UserRole = UserRole.STUDENT
    is_active: bool = True

class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)
    organizationId: Optional[str] = None
    organization_name: Optional[str] = None
    organization_domain: Optional[str] = None
    
    @validator('organizationId', 'organization_name', always=True)
    def validate_organization(cls, v, values):
        """Validate that either organizationId or organization_name is provided."""
        if not v and not values.get('organizationId') and not values.get('organization_name'):
            raise ValueError('Either organizationId or organization_name must be provided')
        return v

class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    """User database schema."""
    id: str
    organizationId: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class User(UserBase):
    """User response schema."""
    id: str
    organizationId: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class UserWithOrganization(User):
    """User with organization details."""
    organization_name: str
    
    class Config:
        from_attributes = True
