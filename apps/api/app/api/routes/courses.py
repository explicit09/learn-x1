from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.base import DataResponse, PaginatedResponse, BaseResponse
from app.schemas.course import Course, CourseCreate, CourseUpdate, CourseWithStats, Enrollment, EnrollmentCreate
from app.services.auth import auth_service
from app.services.prisma import prisma_service

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[Course])
async def list_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """List courses with pagination and filtering."""
    # Build filter conditions
    where = {}
    
    # Organization filter - users can only see courses in their organization
    where["organization_id"] = current_user["organization_id"]
    
    # Status filter
    if status:
        where["status"] = status
    
    # Search filter
    if search:
        where["OR"] = [
            {"title": {"contains": search, "mode": "insensitive"}},
            {"description": {"contains": search, "mode": "insensitive"}}
        ]
    
    # Students can only see published courses
    if current_user["role"] == "student":
        where["status"] = "published"
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get courses
    courses = await prisma_service.get_many(
        model="course",
        where=where,
        skip=skip,
        take=per_page,
        order_by={"title": "asc"}
    )
    
    # Get total count
    total = await prisma_service.count(model="course", where=where)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=courses,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages
        }
    )

@router.post("/", response_model=DataResponse[Course])
async def create_course(course_data: CourseCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Create a new course."""
    # Check permissions - only professors and admins can create courses
    if current_user["role"] not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Professors and admins can only create courses in their own organization
    if course_data.organization_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create course in another organization"
        )
    
    # Create course
    create_data = course_data.dict()
    create_data["organization"] = {"connect": {"id": create_data["organization_id"]}}
    del create_data["organization_id"]
    
    new_course = await prisma_service.create(model="course", data=create_data)
    
    return DataResponse(data=new_course, message="Course created successfully")

@router.get("/{course_id}", response_model=DataResponse[Course])
async def get_course(course_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get course by ID."""
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
    
    # Students can only see published courses
    if current_user["role"] == "student" and course["status"] != "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Course not available"
        )
    
    return DataResponse(data=course)

@router.put("/{course_id}", response_model=DataResponse[Course])
async def update_course(course_id: str, course_update: CourseUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update course by ID."""
    # Get course
    course = await prisma_service.get(model="course", id=course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions - only professors and admins can update courses in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = course_update.dict(exclude_unset=True)
    
    # Update course
    updated_course = await prisma_service.update(
        model="course",
        id=course_id,
        data=update_data
    )
    
    return DataResponse(data=updated_course, message="Course updated successfully")

@router.delete("/{course_id}", response_model=BaseResponse)
async def delete_course(course_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Delete course by ID."""
    # Get course
    course = await prisma_service.get(model="course", id=course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions - only admins can delete courses in their organization
    if current_user["role"] != "admin" or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete course
    await prisma_service.delete(model="course", id=course_id)
    
    return BaseResponse(message="Course deleted successfully")

@router.get("/{course_id}/stats", response_model=DataResponse[CourseWithStats])
async def get_course_stats(course_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get course statistics."""
    # Get course
    course = await prisma_service.get(model="course", id=course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions - only professors and admins can view course stats in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get enrollment count
    enrollment_count = await prisma_service.count(
        model="enrollment",
        where={"course_id": course_id}
    )
    
    # Get material count
    material_count = await prisma_service.count(
        model="material",
        where={"course_id": course_id}
    )
    
    # Get quiz count
    quiz_count = await prisma_service.count(
        model="quiz",
        where={"course_id": course_id}
    )
    
    # Add stats to course
    course_with_stats = {
        **course,
        "enrollment_count": enrollment_count,
        "material_count": material_count,
        "quiz_count": quiz_count
    }
    
    return DataResponse(data=course_with_stats)

@router.post("/{course_id}/enroll", response_model=DataResponse[Enrollment])
async def enroll_in_course(course_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Enroll current user in a course."""
    # Get course
    course = await prisma_service.get(model="course", id=course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course is in user's organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot enroll in course from another organization"
        )
    
    # Check if course is published
    if course["status"] != "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot enroll in unpublished course"
        )
    
    # Check if already enrolled
    existing_enrollments = await prisma_service.get_many(
        model="enrollment",
        where={
            "course_id": course_id,
            "user_id": current_user["id"]
        }
    )
    
    if existing_enrollments and len(existing_enrollments) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    # Create enrollment
    enrollment_data = {
        "course": {"connect": {"id": course_id}},
        "user": {"connect": {"id": current_user["id"]}}
    }
    
    new_enrollment = await prisma_service.create(model="enrollment", data=enrollment_data)
    
    return DataResponse(data=new_enrollment, message="Successfully enrolled in course")

@router.delete("/{course_id}/enroll", response_model=BaseResponse)
async def unenroll_from_course(course_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Unenroll current user from a course."""
    # Find enrollment
    enrollments = await prisma_service.get_many(
        model="enrollment",
        where={
            "course_id": course_id,
            "user_id": current_user["id"]
        }
    )
    
    if not enrollments or len(enrollments) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course"
        )
    
    # Delete enrollment
    await prisma_service.delete(model="enrollment", id=enrollments[0]["id"])
    
    return BaseResponse(message="Successfully unenrolled from course")
