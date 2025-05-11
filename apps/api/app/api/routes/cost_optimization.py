from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user, get_current_admin_user
from app.services.api_cost_optimization import api_cost_optimization_service
from app.schemas.users import User

router = APIRouter()

@router.get("/summary")
async def get_cost_summary(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("month", description="Time period (day, week, month, year)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get a summary of API costs for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's cost data"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month", "year"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month, year"
        )
    
    cost_summary = await api_cost_optimization_service.get_cost_summary(
        organization_id=organization_id,
        time_period=time_period
    )
    
    if "error" in cost_summary:
        raise HTTPException(status_code=400, detail=cost_summary["error"])
    
    return cost_summary

@router.get("/by-user")
async def get_cost_by_user(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("month", description="Time period (day, week, month, year)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get a breakdown of API costs by user for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's cost data"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month", "year"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month, year"
        )
    
    cost_by_user = await api_cost_optimization_service.get_cost_by_user(
        organization_id=organization_id,
        time_period=time_period
    )
    
    if "error" in cost_by_user:
        raise HTTPException(status_code=400, detail=cost_by_user["error"])
    
    return cost_by_user

@router.get("/recommendations")
async def get_cost_optimization_recommendations(
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get cost optimization recommendations for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's cost data"
        )
    
    recommendations = await api_cost_optimization_service.recommend_cost_optimizations(
        organization_id=organization_id
    )
    
    if "error" in recommendations:
        raise HTTPException(status_code=400, detail=recommendations["error"])
    
    return recommendations

@router.get("/recommended-model")
async def get_recommended_model(
    interaction_type: str = Query(..., description="Type of interaction (completion, embedding)"),
    user_role: str = Query(..., description="Role of the user (student, professor, admin, super_admin)"),
    content_complexity: Optional[str] = Query(None, description="Complexity of the content (low, medium, high)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Get the recommended model for a specific interaction type based on user role and content complexity.
    
    This endpoint is available to all authenticated users.
    """
    # Validate interaction type
    if interaction_type not in ["completion", "embedding"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid interaction type. Must be one of: completion, embedding"
        )
    
    # Validate user role
    if user_role not in ["student", "professor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid user role. Must be one of: student, professor, admin, super_admin"
        )
    
    # Validate content complexity if provided
    if content_complexity is not None and content_complexity not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid content complexity. Must be one of: low, medium, high"
        )
    
    recommended_model = await api_cost_optimization_service.get_recommended_model(
        interaction_type=interaction_type,
        user_role=user_role,
        content_complexity=content_complexity
    )
    
    return {"recommended_model": recommended_model}
