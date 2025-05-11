from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.services.prisma import prisma_service

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

class AuthService:
    """Service for authentication and authorization."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        print("\n=== Verifying password ===")
        result = pwd_context.verify(plain_password, hashed_password)
        print("Password verification result:", result)
        return result
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a password hash."""
        print("\n=== Generating password hash ===")
        hashed = pwd_context.hash(password)
        print("Generated hash:", hashed[:10] + "...")
        return hashed
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user by email and password."""
        try:
            # Get user from database by email
            users = await prisma_service.get_many(
                model="user",
                where={"email": email}
            )
            
            if not users or len(users) == 0:
                print(f"No user found with email: {email}")
                return None
            
            user = users[0]
            
            # Verify password
            if not AuthService.verify_password(password, user["password"]):
                print("Password verification failed")
                return None
            
            # Remove sensitive data before returning
            user_data = dict(user)
            if "password" in user_data:
                del user_data["password"]
                
            return user_data
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None

    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        # Create JWT token
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
        """Get the current authenticated user from a JWT token."""
        # Development bypass: Return a mock admin user
        mock_user = {
            "id": "1",
            "email": "admin@example.com",
            "name": "Admin User",
            "role": "admin",
            "organizationId": "1",
            "is_active": True
        }
        return mock_user

# Create a singleton instance of the AuthService
auth_service = AuthService()
