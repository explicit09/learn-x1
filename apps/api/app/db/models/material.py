from sqlalchemy import Column, String, Text, Boolean, ForeignKey, BigInteger, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class Material(Base):
    """Material model for educational content storage."""
    title = Column(String(255), nullable=False)
    description = Column(Text)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    is_processed = Column(Boolean, default=False)
    
    # Relationships
    course = relationship("Course", back_populates="materials")
    uploader = relationship("User", backref="uploaded_materials")
    content = relationship("MaterialContent", back_populates="material", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Material(id={self.id}, title={self.title}, course_id={self.course_id})>"


class MaterialContent(Base):
    """Material content model for storing processed content."""
    material_id = Column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False, index=True)
    content_type = Column(String(50), nullable=False)  # text, audio_transcript, etc.
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    material = relationship("Material", back_populates="content")
    embeddings = relationship("Embedding", back_populates="content", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MaterialContent(id={self.id}, material_id={self.material_id}, content_type={self.content_type})>"


class Embedding(Base):
    """Embedding model for vector storage."""
    material_content_id = Column(UUID(as_uuid=True), ForeignKey("materialcontent.id"), nullable=False, index=True)
    embedding = Column(String, nullable=False)  # Vector stored as string, will use pgvector in production
    
    # Relationships
    content = relationship("MaterialContent", back_populates="embeddings")
    
    def __repr__(self) -> str:
        return f"<Embedding(id={self.id}, material_content_id={self.material_content_id})>"
