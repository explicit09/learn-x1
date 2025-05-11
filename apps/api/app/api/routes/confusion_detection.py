from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import UUID4

from app.schemas.user import User
from app.api.deps import get_current_user, get_current_active_user
from app.services.confusion_detection import confusion_detection_service

router = APIRouter()

@router.post("/detect-text")
async def detect_confusion_in_text(
    text: str = Query(..., description="Text to analyze for confusion signals"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Detect confusion signals in text using pattern matching and NLP."""
    result = await confusion_detection_service.detect_confusion_in_text(text)
    return result

@router.get("/interaction/{interaction_id}")
async def detect_confusion_in_interaction(
    interaction_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Detect confusion in a specific user interaction."""
    result = await confusion_detection_service.detect_confusion_in_interaction(interaction_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.get("/user/{user_id}/patterns")
async def analyze_user_confusion_patterns(
    user_id: str,
    days: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Analyze confusion patterns for a specific user over time."""
    # Check permissions (only allow users to view their own data or professors/admins)
    if current_user.id != user_id and current_user.role not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's data"
        )
    
    result = await confusion_detection_service.analyze_user_confusion_patterns(user_id, days)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    return result

@router.get("/user/{user_id}/interventions")
async def get_intervention_recommendations(
    user_id: str,
    topic_id: Optional[str] = Query(None, description="Optional topic ID to focus on"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get personalized intervention recommendations for a confused user."""
    # Check permissions (only allow users to view their own data or professors/admins)
    if current_user.id != user_id and current_user.role not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's data"
        )
    
    result = await confusion_detection_service.get_intervention_recommendations(user_id, topic_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    return result

@router.get("/organization/{organization_id}/hotspots")
async def detect_class_confusion_hotspots(
    organization_id: str,
    days: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Detect confusion hotspots across an entire class or organization."""
    # Check permissions (only allow professors/admins)
    if current_user.role not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors and admins can access organization-wide confusion data"
        )
    
    # Check if user belongs to the organization
    if current_user.organization_id != organization_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization's data"
        )
    
    result = await confusion_detection_service.detect_class_confusion_hotspots(organization_id, days)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    return result
