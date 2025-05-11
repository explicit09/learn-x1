from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class User(Base):
    """User model for authentication and authorization."""
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization.id"), index=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organization = relationship("Organization", backref="users")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class UserPreference(Base):
    """User preferences for personalization."""
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    learning_style = Column(String(50))
    interests = Column(String, nullable=True)  # JSON stored as string
    ui_preferences = Column(String, nullable=True)  # JSON stored as string
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id}, learning_style={self.learning_style})>"
