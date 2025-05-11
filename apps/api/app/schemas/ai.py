from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum

class AIModelType(str, Enum):
    """AI model type enumeration."""
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    CUSTOM = "custom"

class AIInteractionType(str, Enum):
    """AI interaction type enumeration."""
    QUESTION = "question"
    EXPLANATION = "explanation"
    QUIZ_GENERATION = "quiz_generation"
    SUMMARY = "summary"

class AIInteractionBase(BaseModel):
    """Base AI interaction schema."""
    query: str
    interaction_type: AIInteractionType = AIInteractionType.QUESTION
    context_ids: Optional[List[UUID4]] = None  # IDs of related content chunks
    model: AIModelType = AIModelType.GPT_3_5

class AIInteractionCreate(AIInteractionBase):
    """AI interaction creation schema."""
    user_id: UUID4
    course_id: Optional[UUID4] = None
    material_id: Optional[UUID4] = None

class AIInteraction(AIInteractionBase):
    """AI interaction response schema."""
    id: UUID4
    user_id: UUID4
    course_id: Optional[UUID4] = None
    material_id: Optional[UUID4] = None
    response: str
    tokens_used: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class AISearchQuery(BaseModel):
    """AI semantic search query schema."""
    query: str
    course_id: Optional[UUID4] = None
    limit: int = 5

class AISearchResult(BaseModel):
    """AI semantic search result schema."""
    content_chunk_id: UUID4
    content: str
    material_id: UUID4
    material_title: str
    similarity: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        orm_mode = True

class AIQuizGenerationRequest(BaseModel):
    """AI quiz generation request schema."""
    material_id: UUID4
    num_questions: int = 5
    question_types: List[str] = ["multiple_choice", "true_false"]
    difficulty: str = "medium"  # easy, medium, hard

class AIExplanationRequest(BaseModel):
    """AI explanation request schema."""
    content: str
    material_id: Optional[UUID4] = None
    detail_level: str = "medium"  # basic, medium, advanced

class LearningStyleUpdate(BaseModel):
    """Learning style update schema."""
    visual_score: Optional[int] = Field(None, ge=1, le=10)
    auditory_score: Optional[int] = Field(None, ge=1, le=10)
    reading_score: Optional[int] = Field(None, ge=1, le=10)
    kinesthetic_score: Optional[int] = Field(None, ge=1, le=10)
