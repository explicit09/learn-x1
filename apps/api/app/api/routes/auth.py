from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.schemas.auth import Token, LoginRequest, RegisterRequest, PasswordResetRequest, PasswordResetConfirmRequest
from app.schemas.base import DataResponse, BaseResponse
from app.schemas.user import User, UserCreate, UserRole
from app.services.auth import auth_service
from app.services.prisma import prisma_service

router = APIRouter()

@router.post("/login", response_model=DataResponse[Token])
async def login(login_data: LoginRequest) -> Any:
    """Authenticate user and return access token."""
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user["id"], "org": user["organizationId"], "role": user["role"]},
        expires_delta=access_token_expires,
    )
    
    # Calculate expiration time for client
    expires_at = datetime.utcnow() + access_token_expires
    
    return DataResponse(
        data=Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at
        ),
        message="Login successful"
    )

@router.post("/register", response_model=DataResponse[User])
async def register(register_data: RegisterRequest) -> Any:
    """Register a new user and optionally create a new organization."""
    print("\n=== Starting registration process ===")
    print("Registration data:", register_data.dict())
    
    try:
        # Check if email already exists
        print("\nChecking for existing users...")
        existing_users = await prisma_service.get_many(
            model="user",
            where={"email": register_data.email}
        )
        print("Existing users:", existing_users)
        
        if existing_users and len(existing_users) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Handle organization
        print("\nHandling organization...")
        organization_id = register_data.organizationId
        print("Initial organization_id:", organization_id)
        
        if not organization_id and register_data.organization_name:
            # Create new organization
            print("\nCreating new organization...")
            org_data = {
                "name": register_data.organization_name,
                "domain": register_data.organization_domain,
                "is_active": True
            }
            print("Organization data:", org_data)
            
            try:
                new_org = await prisma_service.create(model="organization", data=org_data)
                print("Created organization:", new_org)
                organization_id = new_org["id"]
                print("New organization_id:", organization_id)
            except Exception as e:
                print("Error creating organization:", str(e))
                print("Error details:", e.__dict__)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating organization: {str(e)}"
                )
        
        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID or name is required"
            )
        
        # Create user
        print("\nPreparing user data...")
        user_data = {
            "email": register_data.email,
            "password": auth_service.get_password_hash(register_data.password),
            "name": register_data.name,
            "role": UserRole.ADMIN,  # First user in an org is admin by default
            "is_active": True,
            "organizationId": organization_id
        }
        print("User data:", user_data)
        
        # Verify organization exists
        print("\nVerifying organization exists...")
        org = await prisma_service.get(model="organization", id=organization_id)
        print("Found organization:", org)
        
        if not org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found"
            )
        
        # Create user
        print("\nCreating user...")
        new_user = await prisma_service.create(model="user", data=user_data)
        print("Created user:", new_user)
        
        # Remove password from response
        if "password" in new_user:
            del new_user["password"]
        
        print("\n=== Registration successful ===")
        return DataResponse(
            data=new_user,
            message="User registered successfully"
        )
    except HTTPException as e:
        print("\n=== Registration failed with HTTP error ===")
        print("Error:", str(e))
        raise e
    except Exception as e:
        print("\n=== Registration failed with unexpected error ===")
        print("Error:", str(e))
        print("Error details:", e.__dict__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )
    


@router.post("/password-reset", response_model=BaseResponse)
async def request_password_reset(reset_data: PasswordResetRequest) -> Any:
    """Request a password reset link."""
    # Check if user exists
    users = await prisma_service.get_many(
        model="user",
        where={"email": reset_data.email}
    )
    
    if not users or len(users) == 0:
        # Don't reveal that email doesn't exist for security
        return BaseResponse(message="If your email is registered, you will receive a password reset link")
    
    # TODO: Implement actual email sending with reset token
    # For now, just return success message
    
    return BaseResponse(message="If your email is registered, you will receive a password reset link")

@router.post("/password-reset/confirm", response_model=BaseResponse)
async def confirm_password_reset(confirm_data: PasswordResetConfirmRequest) -> Any:
    """Confirm password reset with token."""
    # TODO: Implement actual token verification and password reset
    # For now, just return error
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset confirmation not implemented yet"
    )
