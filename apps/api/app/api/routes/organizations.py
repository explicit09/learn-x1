from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.base import DataResponse, BaseResponse
from app.schemas.organization import Organization, OrganizationCreate, OrganizationUpdate, OrganizationWithStats
from app.services.auth import auth_service
from app.services.prisma import prisma_service

router = APIRouter()

@router.get("/my-organization", response_model=DataResponse[Organization])
async def get_my_organization(current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get current user's organization."""
    organization = await prisma_service.get(
        model="organization",
        id=current_user["organization_id"]
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return DataResponse(data=organization)

@router.put("/my-organization", response_model=DataResponse[Organization])
async def update_my_organization(
    org_update: OrganizationUpdate, 
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """Update current user's organization."""
    # Check permissions - only admins can update organization
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = org_update.dict(exclude_unset=True)
    
    # Update organization
    updated_org = await prisma_service.update(
        model="organization",
        id=current_user["organization_id"],
        data=update_data
    )
    
    return DataResponse(data=updated_org, message="Organization updated successfully")

@router.get("/my-organization/stats", response_model=DataResponse[OrganizationWithStats])
async def get_my_organization_stats(current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get current user's organization with statistics."""
    # Check permissions - only admins can view organization stats
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get organization
    organization = await prisma_service.get(
        model="organization",
        id=current_user["organization_id"]
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get user count
    user_count = await prisma_service.count(
        model="user",
        where={"organization_id": current_user["organization_id"]}
    )
    
    # Get course count
    course_count = await prisma_service.count(
        model="course",
        where={"organization_id": current_user["organization_id"]}
    )
    
    # Add stats to organization
    organization_with_stats = {
        **organization,
        "user_count": user_count,
        "course_count": course_count
    }
    
    return DataResponse(data=organization_with_stats)
