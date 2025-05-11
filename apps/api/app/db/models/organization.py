from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class Organization(Base):
    """Organization model for multi-tenant architecture."""
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
