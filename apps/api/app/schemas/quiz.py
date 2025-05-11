from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum

class QuestionType(str, Enum):
    """Question type enumeration."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

class QuizBase(BaseModel):
    """Base quiz schema with common fields."""
    title: str
    description: str
    time_limit_minutes: Optional[int] = None
    passing_score: int = 70
    is_published: bool = False
    randomize_questions: bool = False

class QuizCreate(QuizBase):
    """Quiz creation schema."""
    course_id: UUID4
    material_id: Optional[UUID4] = None

class QuizUpdate(BaseModel):
    """Quiz update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score: Optional[int] = None
    is_published: Optional[bool] = None
    randomize_questions: Optional[bool] = None

class Quiz(QuizBase):
    """Quiz response schema."""
    id: UUID4
    course_id: UUID4
    material_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class QuestionBase(BaseModel):
    """Base question schema with common fields."""
    question_text: str
    question_type: QuestionType
    points: int = 1
    order: int = 0
    options: Optional[List[Dict[str, Any]]] = None  # For multiple choice
    correct_answer: Any  # Can be string, list of strings, or complex object
    explanation: Optional[str] = None

class QuestionCreate(QuestionBase):
    """Question creation schema."""
    quiz_id: UUID4

class QuestionUpdate(BaseModel):
    """Question update schema."""
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    points: Optional[int] = None
    order: Optional[int] = None
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Optional[Any] = None
    explanation: Optional[str] = None

class Question(QuestionBase):
    """Question response schema."""
    id: UUID4
    quiz_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class SubmissionBase(BaseModel):
    """Base submission schema."""
    answers: Dict[str, Any]  # Question ID to answer mapping
    time_spent_seconds: int

class SubmissionCreate(SubmissionBase):
    """Submission creation schema."""
    quiz_id: UUID4
    user_id: UUID4

class Submission(SubmissionBase):
    """Submission response schema."""
    id: UUID4
    quiz_id: UUID4
    user_id: UUID4
    score: float
    passed: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class SubmissionWithDetails(Submission):
    """Submission with question details and feedback."""
    quiz_title: str
    question_results: List[Dict[str, Any]]
    
    class Config:
        orm_mode = True
