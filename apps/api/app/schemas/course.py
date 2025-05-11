from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum

class CourseStatus(str, Enum):
    """Course status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CourseBase(BaseModel):
    """Base course schema with common fields."""
    title: str
    description: str
    status: CourseStatus = CourseStatus.DRAFT

class CourseCreate(CourseBase):
    """Course creation schema."""
    organization_id: UUID4

class CourseUpdate(BaseModel):
    """Course update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CourseStatus] = None

class Course(CourseBase):
    """Course response schema."""
    id: UUID4
    organization_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class CourseWithStats(Course):
    """Course with additional statistics."""
    enrollment_count: int
    material_count: int
    quiz_count: int
    
    class Config:
        orm_mode = True

class EnrollmentBase(BaseModel):
    """Base enrollment schema."""
    course_id: UUID4
    user_id: UUID4

class EnrollmentCreate(EnrollmentBase):
    """Enrollment creation schema."""
    pass

class Enrollment(EnrollmentBase):
    """Enrollment response schema."""
    id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class EnrollmentWithDetails(Enrollment):
    """Enrollment with course and user details."""
    course_title: str
    user_name: str
    progress: float = 0.0
    
    class Config:
        orm_mode = True
