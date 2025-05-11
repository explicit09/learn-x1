from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user, get_current_admin_user
from app.services.performance_monitoring import performance_monitoring_service
from app.services.api_usage import api_usage_service
from app.schemas.users import User

router = APIRouter()

@router.get("/performance/response-time")
async def get_response_time_metrics(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("day", description="Time period (day, week, month)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get response time metrics for AI interactions.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's metrics"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month"
        )
    
    metrics = await performance_monitoring_service.get_response_time_metrics(
        organization_id=organization_id,
        time_period=time_period
    )
    
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return metrics

@router.get("/performance/error-rate")
async def get_error_rate_metrics(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("day", description="Time period (day, week, month)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get error rate metrics for AI interactions.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's metrics"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month"
        )
    
    metrics = await performance_monitoring_service.get_error_rate_metrics(
        organization_id=organization_id,
        time_period=time_period
    )
    
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return metrics

@router.get("/performance/token-usage")
async def get_token_usage_metrics(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("day", description="Time period (day, week, month)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get token usage metrics for AI interactions.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's metrics"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month"
        )
    
    metrics = await performance_monitoring_service.get_token_usage_metrics(
        organization_id=organization_id,
        time_period=time_period
    )
    
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return metrics

@router.get("/usage/summary")
async def get_api_usage_summary(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("day", description="Time period (day, week, month)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get API usage summary for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's usage data"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month"
        )
    
    usage_summary = await api_usage_service.get_usage_summary(
        organization_id=organization_id,
        time_period=time_period
    )
    
    return usage_summary

@router.get("/usage/by-user")
async def get_api_usage_by_user(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("day", description="Time period (day, week, month)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get API usage breakdown by user for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's usage data"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month"
        )
    
    usage_by_user = await api_usage_service.get_usage_by_user(
        organization_id=organization_id,
        time_period=time_period
    )
    
    return usage_by_user
