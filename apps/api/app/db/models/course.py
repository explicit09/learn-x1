from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class Course(Base):
    """Course model for educational content organization."""
    title = Column(String(255), nullable=False)
    description = Column(Text)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organization = relationship("Organization", backref="courses")
    creator = relationship("User", backref="created_courses")
    materials = relationship("Material", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Course(id={self.id}, title={self.title})>"


class CourseEnrollment(Base):
    """Course enrollment model for student-course relationships."""
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # student, professor, teaching_assistant
    
    # Relationships
    course = relationship("Course", back_populates="enrollments")
    user = relationship("User", backref="enrollments")
    
    def __repr__(self) -> str:
        return f"<CourseEnrollment(course_id={self.course_id}, user_id={self.user_id}, role={self.role})>"
