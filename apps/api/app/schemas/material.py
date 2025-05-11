from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum

class MaterialType(str, Enum):
    """Material type enumeration."""
    LESSON = "lesson"
    ARTICLE = "article"
    VIDEO = "video"
    DOCUMENT = "document"
    INTERACTIVE = "interactive"

class ContentType(str, Enum):
    """Content type enumeration."""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    VIDEO_URL = "video_url"
    DOCUMENT_URL = "document_url"
    INTERACTIVE_URL = "interactive_url"

class MaterialBase(BaseModel):
    """Base material schema with common fields."""
    title: str
    description: str
    type: MaterialType = MaterialType.LESSON
    order: int = 0
    is_published: bool = False

class MaterialCreate(MaterialBase):
    """Material creation schema."""
    course_id: UUID4

class MaterialUpdate(BaseModel):
    """Material update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[MaterialType] = None
    order: Optional[int] = None
    is_published: Optional[bool] = None

class Material(MaterialBase):
    """Material response schema."""
    id: UUID4
    course_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ContentBase(BaseModel):
    """Base content schema with common fields."""
    type: ContentType
    content: str
    order: int = 0

class ContentCreate(ContentBase):
    """Content creation schema."""
    material_id: UUID4

class ContentUpdate(BaseModel):
    """Content update schema."""
    type: Optional[ContentType] = None
    content: Optional[str] = None
    order: Optional[int] = None

class Content(ContentBase):
    """Content response schema."""
    id: UUID4
    material_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ContentChunkBase(BaseModel):
    """Base content chunk schema for vector search."""
    content: str
    metadata: Optional[dict] = Field(default_factory=dict)

class ContentChunkCreate(ContentChunkBase):
    """Content chunk creation schema."""
    content_id: UUID4

class ContentChunk(ContentChunkBase):
    """Content chunk response schema."""
    id: UUID4
    content_id: UUID4
    embedding: Optional[Any] = None  # Vector representation
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
