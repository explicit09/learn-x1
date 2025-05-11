from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.base import DataResponse, PaginatedResponse, BaseResponse
from app.schemas.user import User, UserCreate, UserUpdate, UserWithOrganization
from app.services.auth import auth_service
from app.services.prisma import prisma_service

router = APIRouter()

@router.get("/me", response_model=DataResponse[User])
async def get_current_user_info(current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get current user information."""
    return DataResponse(data=current_user)

@router.put("/me", response_model=DataResponse[User])
async def update_current_user(user_update: UserUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update current user information."""
    # Prepare update data
    update_data = user_update.dict(exclude_unset=True)
    
    # Don't allow role change through this endpoint
    if "role" in update_data:
        del update_data["role"]
    
    # Update user
    updated_user = await prisma_service.update(
        model="user",
        id=current_user["id"],
        data=update_data
    )
    
    return DataResponse(data=updated_user, message="User updated successfully")

@router.get("/", response_model=PaginatedResponse[User])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    organization_id: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """List users with pagination and filtering."""
    # Check permissions - only admins can list users
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Build filter conditions
    where = {}
    
    # Organization filter - admins can only see users in their organization
    where["organization_id"] = current_user["organization_id"]
    
    # Additional filters
    if role:
        where["role"] = role
    
    if search:
        # Simple search by name or email
        where["OR"] = [
            {"name": {"contains": search, "mode": "insensitive"}},
            {"email": {"contains": search, "mode": "insensitive"}}
        ]
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get users
    users = await prisma_service.get_many(
        model="user",
        where=where,
        skip=skip,
        take=per_page,
        order_by={"name": "asc"}
    )
    
    # Get total count
    total = await prisma_service.count(model="user", where=where)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=users,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages
        }
    )

@router.post("/", response_model=DataResponse[User])
async def create_user(user_data: UserCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Create a new user."""
    # Check permissions - only admins can create users
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if email already exists
    existing_users = await prisma_service.get_many(
        model="user",
        where={"email": user_data.email}
    )
    
    if existing_users and len(existing_users) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Admins can only create users in their own organization
    if user_data.organization_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create user in another organization"
        )
    
    # Create user
    create_data = user_data.dict()
    create_data["password"] = auth_service.get_password_hash(create_data["password"])
    create_data["organization"] = {"connect": {"id": create_data["organization_id"]}}
    del create_data["organization_id"]
    
    new_user = await prisma_service.create(model="user", data=create_data)
    
    # Remove password from response
    if "password" in new_user:
        del new_user["password"]
    
    return DataResponse(data=new_user, message="User created successfully")

@router.get("/{user_id}", response_model=DataResponse[User])
async def get_user(user_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get user by ID."""
    # Get user
    user = await prisma_service.get(model="user", id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions - users can only see themselves or admins can see users in their organization
    if user_id != current_user["id"] and (current_user["role"] != "admin" or user["organization_id"] != current_user["organization_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Remove password from response
    if "password" in user:
        del user["password"]
    
    return DataResponse(data=user)

@router.put("/{user_id}", response_model=DataResponse[User])
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update user by ID."""
    # Get user
    user = await prisma_service.get(model="user", id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions - admins can only update users in their organization
    if current_user["role"] != "admin" or user["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = user_update.dict(exclude_unset=True)
    
    # Update user
    updated_user = await prisma_service.update(
        model="user",
        id=user_id,
        data=update_data
    )
    
    # Remove password from response
    if "password" in updated_user:
        del updated_user["password"]
    
    return DataResponse(data=updated_user, message="User updated successfully")

@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(user_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Delete user by ID."""
    # Get user
    user = await prisma_service.get(model="user", id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions - admins can only delete users in their organization
    if current_user["role"] != "admin" or user["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prevent self-deletion
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Delete user
    await prisma_service.delete(model="user", id=user_id)
    
    return BaseResponse(message="User deleted successfully")
