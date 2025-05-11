from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.base import DataResponse, PaginatedResponse, BaseResponse
from app.schemas.material import Material, MaterialCreate, MaterialUpdate, Content, ContentCreate, ContentUpdate
from app.services.auth import auth_service
from app.services.prisma import prisma_service

router = APIRouter()

@router.get("/course/{course_id}", response_model=PaginatedResponse[Material])
async def list_course_materials(
    course_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    published_only: bool = False,
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """List materials for a course with pagination."""
    # Get course
    course = await prisma_service.get(model="course", id=course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions - users can only see courses in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only see published courses and materials
    if current_user["role"] == "student":
        if course["status"] != "published":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Course not available"
            )
        published_only = True
    
    # Build filter conditions
    where = {"course_id": course_id}
    
    # Filter by published status
    if published_only:
        where["is_published"] = True
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get materials
    materials = await prisma_service.get_many(
        model="material",
        where=where,
        skip=skip,
        take=per_page,
        order_by={"order": "asc"}
    )
    
    # Get total count
    total = await prisma_service.count(model="material", where=where)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=materials,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages
        }
    )

@router.post("/", response_model=DataResponse[Material])
async def create_material(material_data: MaterialCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Create a new material."""
    # Get course
    course = await prisma_service.get(model="course", id=material_data.course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions - only professors and admins can create materials in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Create material
    create_data = material_data.dict()
    create_data["course"] = {"connect": {"id": create_data["course_id"]}}
    del create_data["course_id"]
    
    new_material = await prisma_service.create(model="material", data=create_data)
    
    return DataResponse(data=new_material, message="Material created successfully")

@router.get("/{material_id}", response_model=DataResponse[Material])
async def get_material(material_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get material by ID."""
    # Get material
    material = await prisma_service.get(model="material", id=material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - users can only see materials in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only see published courses and materials
    if current_user["role"] == "student" and (course["status"] != "published" or not material["is_published"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Material not available"
        )
    
    return DataResponse(data=material)

@router.put("/{material_id}", response_model=DataResponse[Material])
async def update_material(material_id: str, material_update: MaterialUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update material by ID."""
    # Get material
    material = await prisma_service.get(model="material", id=material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - only professors and admins can update materials in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = material_update.dict(exclude_unset=True)
    
    # Update material
    updated_material = await prisma_service.update(
        model="material",
        id=material_id,
        data=update_data
    )
    
    return DataResponse(data=updated_material, message="Material updated successfully")

@router.delete("/{material_id}", response_model=BaseResponse)
async def delete_material(material_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Delete material by ID."""
    # Get material
    material = await prisma_service.get(model="material", id=material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - only professors and admins can delete materials in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete material
    await prisma_service.delete(model="material", id=material_id)
    
    return BaseResponse(message="Material deleted successfully")

# Content endpoints
@router.get("/{material_id}/content", response_model=PaginatedResponse[Content])
async def list_material_content(
    material_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """List content for a material with pagination."""
    # Get material
    material = await prisma_service.get(model="material", id=material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - users can only see content in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only see published courses and materials
    if current_user["role"] == "student" and (course["status"] != "published" or not material["is_published"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content not available"
        )
    
    # Build filter conditions
    where = {"material_id": material_id}
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get content
    content = await prisma_service.get_many(
        model="content",
        where=where,
        skip=skip,
        take=per_page,
        order_by={"order": "asc"}
    )
    
    # Get total count
    total = await prisma_service.count(model="content", where=where)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=content,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages
        }
    )

@router.post("/content", response_model=DataResponse[Content])
async def create_content(content_data: ContentCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Create new content for a material."""
    # Get material
    material = await prisma_service.get(model="material", id=content_data.material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - only professors and admins can create content in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Create content
    create_data = content_data.dict()
    create_data["material"] = {"connect": {"id": create_data["material_id"]}}
    del create_data["material_id"]
    
    new_content = await prisma_service.create(model="content", data=create_data)
    
    # Create content chunks for vector search if AI features are enabled
    # This would be implemented in a separate service
    
    return DataResponse(data=new_content, message="Content created successfully")

@router.get("/content/{content_id}", response_model=DataResponse[Content])
async def get_content(content_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get content by ID."""
    # Get content
    content = await prisma_service.get(model="content", id=content_id)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get material
    material = await prisma_service.get(model="material", id=content["material_id"])
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - users can only see content in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only see published courses and materials
    if current_user["role"] == "student" and (course["status"] != "published" or not material["is_published"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content not available"
        )
    
    return DataResponse(data=content)

@router.put("/content/{content_id}", response_model=DataResponse[Content])
async def update_content(content_id: str, content_update: ContentUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update content by ID."""
    # Get content
    content = await prisma_service.get(model="content", id=content_id)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get material
    material = await prisma_service.get(model="material", id=content["material_id"])
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - only professors and admins can update content in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = content_update.dict(exclude_unset=True)
    
    # Update content
    updated_content = await prisma_service.update(
        model="content",
        id=content_id,
        data=update_data
    )
    
    # Update content chunks for vector search if content changed and AI features are enabled
    # This would be implemented in a separate service
    
    return DataResponse(data=updated_content, message="Content updated successfully")

@router.delete("/content/{content_id}", response_model=BaseResponse)
async def delete_content(content_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Delete content by ID."""
    # Get content
    content = await prisma_service.get(model="content", id=content_id)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get material
    material = await prisma_service.get(model="material", id=content["material_id"])
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check permissions - only professors and admins can delete content in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete content
    await prisma_service.delete(model="content", id=content_id)
    
    # Delete associated content chunks if AI features are enabled
    # This would be implemented in a separate service
    
    return BaseResponse(message="Content deleted successfully")
