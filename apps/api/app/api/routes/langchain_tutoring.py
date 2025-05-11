from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.deps import get_current_user, get_current_active_user
from app.services.langchain_tutoring import langchain_tutoring_service
from app.schemas.user import User

router = APIRouter()

# Request and response models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class QuestionRequest(BaseModel):
    question: str = Field(..., description="The question to answer")
    chat_history: Optional[List[ChatMessage]] = Field(None, description="Previous messages in the conversation")
    tutoring_mode: Optional[str] = Field("default", description="Mode of tutoring (default, beginner, advanced, socratic)")
    course_id: Optional[str] = Field(None, description="ID of the course the question is related to")
    confusion_level: Optional[int] = Field(None, description="Level of confusion (1-10) expressed by the user")

class QuestionResponse(BaseModel):
    answer: str = Field(..., description="The answer to the question")
    has_context: bool = Field(..., description="Whether relevant context was found")
    tutoring_mode: str = Field(..., description="Mode of tutoring used")
    timestamp: str = Field(..., description="Timestamp of the response")

class ConceptRequest(BaseModel):
    concept: str = Field(..., description="The concept to explain")
    detail_level: Optional[str] = Field("medium", description="Level of detail (basic, medium, advanced)")
    course_id: Optional[str] = Field(None, description="ID of the course the concept is related to")

class ConceptResponse(BaseModel):
    concept: str = Field(..., description="The concept that was explained")
    explanation: str = Field(..., description="The explanation of the concept")
    detail_level: str = Field(..., description="Level of detail provided")
    has_context: bool = Field(..., description="Whether relevant context was found")
    timestamp: str = Field(..., description="Timestamp of the response")

class StudyPlanRequest(BaseModel):
    topic: str = Field(..., description="The topic to create a study plan for")
    learning_goal: str = Field(..., description="The learning goal or objective")
    duration_days: Optional[int] = Field(7, description="Duration of the study plan in days")
    course_id: Optional[str] = Field(None, description="ID of the course the topic is related to")

class StudyPlanResponse(BaseModel):
    topic: str = Field(..., description="The topic of the study plan")
    learning_goal: str = Field(..., description="The learning goal or objective")
    duration_days: int = Field(..., description="Duration of the study plan in days")
    study_plan: str = Field(..., description="The generated study plan")
    has_context: bool = Field(..., description="Whether relevant context was found")
    timestamp: str = Field(..., description="Timestamp of the response")

class AssessmentRequest(BaseModel):
    question: str = Field(..., description="The question that was asked")
    student_answer: str = Field(..., description="The student's answer to assess")
    course_id: Optional[str] = Field(None, description="ID of the course the question is related to")

class AssessmentResponse(BaseModel):
    question: str = Field(..., description="The question that was asked")
    student_answer: str = Field(..., description="The student's answer that was assessed")
    assessment: str = Field(..., description="The assessment of the student's answer")
    has_context: bool = Field(..., description="Whether relevant context was found")
    timestamp: str = Field(..., description="Timestamp of the response")

@router.post("/question", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def answer_question(request: QuestionRequest, current_user: User = Depends(get_current_active_user)):
    """Answer a question using LangChain and vector search for context."""
    # Convert chat history to the format expected by the service
    chat_history = None
    if request.chat_history:
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history
        ]
    
    response = await langchain_tutoring_service.answer_question(
        question=request.question,
        chat_history=chat_history,
        tutoring_mode=request.tutoring_mode,
        user_id=str(current_user.id),
        course_id=request.course_id,
        confusion_level=request.confusion_level
    )
    
    return response

@router.post("/explain", response_model=ConceptResponse, status_code=status.HTTP_200_OK)
async def explain_concept(request: ConceptRequest, current_user: User = Depends(get_current_active_user)):
    """Explain a concept using LangChain and vector search for context."""
    response = await langchain_tutoring_service.explain_concept(
        concept=request.concept,
        detail_level=request.detail_level,
        user_id=str(current_user.id),
        course_id=request.course_id
    )
    
    return response

@router.post("/study-plan", response_model=StudyPlanResponse, status_code=status.HTTP_200_OK)
async def generate_study_plan(request: StudyPlanRequest, current_user: User = Depends(get_current_active_user)):
    """Generate a personalized study plan for a topic."""
    response = await langchain_tutoring_service.generate_study_plan(
        topic=request.topic,
        learning_goal=request.learning_goal,
        duration_days=request.duration_days,
        user_id=str(current_user.id),
        course_id=request.course_id
    )
    
    return response

@router.post("/assess", response_model=AssessmentResponse, status_code=status.HTTP_200_OK)
async def assess_answer(request: AssessmentRequest, current_user: User = Depends(get_current_active_user)):
    """Assess a student's answer to a question."""
    response = await langchain_tutoring_service.assess_answer(
        question=request.question,
        student_answer=request.student_answer,
        user_id=str(current_user.id),
        course_id=request.course_id
    )
    
    return response
