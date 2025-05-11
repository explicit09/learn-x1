from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from pydantic import UUID4

from app.schemas.user import User
from app.api.deps import get_current_user
from app.services.personalization import personalization_service

router = APIRouter()

@router.get("/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user preferences for personalization."""
    preferences = await personalization_service.get_user_preferences(current_user.id)
    return preferences

@router.put("/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any] = Body(..., description="User preferences to update"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user preferences."""
    success = await personalization_service.update_user_preferences(
        user_id=current_user.id,
        preferences=preferences
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )
    
    # Get updated preferences
    updated_preferences = await personalization_service.get_user_preferences(current_user.id)
    
    return {
        "message": "Preferences updated successfully",
        "preferences": updated_preferences
    }

@router.get("/recommendations")
async def get_personalized_recommendations(
    limit: int = Query(5, description="Maximum number of recommendations to return"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get personalized content recommendations for a user."""
    recommendations = await personalization_service.get_personalized_recommendations(
        user_id=current_user.id,
        limit=limit
    )
    
    return {
        "recommendations": recommendations,
        "recommendation_count": len(recommendations)
    }

@router.get("/study-plan")
async def get_personalized_study_plan(
    topic_id: Optional[str] = Query(None, description="Optional topic ID to focus on"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate a personalized study plan for a user."""
    study_plan = await personalization_service.generate_personalized_study_plan(
        user_id=current_user.id,
        topic_id=topic_id
    )
    
    if "error" in study_plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=study_plan["error"]
        )
    
    return study_plan

@router.get("/adaptive-difficulty")
async def get_adaptive_difficulty(
    topic_id: Optional[str] = Query(None, description="Optional topic ID to focus on"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get adaptive difficulty level for a user based on their performance."""
    difficulty = await personalization_service.get_adaptive_difficulty(
        user_id=current_user.id,
        topic_id=topic_id
    )
    
    return {
        "user_id": current_user.id,
        "topic_id": topic_id,
        "difficulty_level": difficulty
    }

@router.get("/ui-settings")
async def get_personalized_ui_settings(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get personalized UI settings for a user."""
    ui_settings = await personalization_service.get_personalized_ui_settings(
        user_id=current_user.id
    )
    
    return ui_settings
