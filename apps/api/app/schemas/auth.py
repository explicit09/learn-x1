from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    """Token schema for authentication responses."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class TokenData(BaseModel):
    """Token data schema for decoded JWT tokens."""
    user_id: str
    organizationId: str
    role: str
    exp: datetime

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    """Registration request schema."""
    email: EmailStr
    password: str
    name: str
    organizationId: Optional[str] = None
    organization_name: Optional[str] = None
    organization_domain: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword",
                "name": "John Doe",
                "organizationId": "uuid-string",  # Optional if creating new org
                "organization_name": "Demo University",  # Required if org_id not provided
                "organization_domain": "demo-university.edu"  # Optional
            }
        }

class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8)
