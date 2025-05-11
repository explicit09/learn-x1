from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_current_admin_user
from app.services.performance_monitoring import performance_monitoring_service
from app.services.api_cost_optimization import api_cost_optimization_service
from app.schemas.users import User

router = APIRouter()

@router.get("/summary")
async def get_analytics_summary(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("month", description="Time period (day, week, month, year)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get a comprehensive summary of AI analytics for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's analytics data"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month", "year"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month, year"
        )
    
    # Get cost summary
    cost_summary = await api_cost_optimization_service.get_cost_summary(
        organization_id=organization_id,
        time_period=time_period
    )
    
    # Get performance metrics
    performance_metrics = await performance_monitoring_service.get_response_time_metrics(
        organization_id=organization_id,
        time_period=time_period
    )
    
    # Get error rates
    error_rates = await performance_monitoring_service.get_error_rates(
        organization_id=organization_id,
        time_period=time_period
    )
    
    # Combine all data into a comprehensive dashboard summary
    return {
        "time_period": time_period,
        "cost_metrics": {
            "total_cost": cost_summary.get("total_cost", 0),
            "total_tokens": cost_summary.get("total_tokens", 0),
            "interaction_count": cost_summary.get("interaction_count", 0),
            "average_cost_per_interaction": cost_summary.get("average_cost_per_interaction", 0),
            "cost_by_type": cost_summary.get("cost_by_type", []),
            "cost_by_model": cost_summary.get("cost_by_model", [])
        },
        "performance_metrics": {
            "average_response_time": performance_metrics.get("average_response_time", 0),
            "p90_response_time": performance_metrics.get("p90_response_time", 0),
            "p95_response_time": performance_metrics.get("p95_response_time", 0),
            "p99_response_time": performance_metrics.get("p99_response_time", 0),
            "response_time_by_model": performance_metrics.get("response_time_by_model", []),
            "response_time_by_type": performance_metrics.get("response_time_by_type", [])
        },
        "error_metrics": {
            "total_errors": error_rates.get("total_errors", 0),
            "error_rate": error_rates.get("error_rate", 0),
            "errors_by_type": error_rates.get("errors_by_type", []),
            "errors_by_model": error_rates.get("errors_by_model", [])
        }
    }

@router.get("/user-metrics")
async def get_user_metrics(
    organization_id: str = Query(..., description="Organization ID"),
    time_period: str = Query("month", description="Time period (day, week, month, year)"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get AI usage metrics by user for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's analytics data"
        )
    
    # Validate time period
    if time_period not in ["day", "week", "month", "year"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid time period. Must be one of: day, week, month, year"
        )
    
    # Get cost by user
    cost_by_user = await api_cost_optimization_service.get_cost_by_user(
        organization_id=organization_id,
        time_period=time_period
    )
    
    # Get performance metrics by user (if available)
    performance_by_user = await performance_monitoring_service.get_metrics_by_user(
        organization_id=organization_id,
        time_period=time_period
    )
    
    # Combine user metrics
    user_metrics = []
    
    # Process cost by user data
    for user_cost in cost_by_user.get("cost_by_user", []):
        user_id = user_cost.get("user_id")
        user_metric = {
            "user_id": user_id,
            "user_email": user_cost.get("user_email", ""),
            "user_name": user_cost.get("user_name", ""),
            "cost_metrics": {
                "interaction_count": user_cost.get("count", 0),
                "total_cost": user_cost.get("cost", 0),
                "total_tokens": user_cost.get("tokens", 0),
                "percentage_of_total": user_cost.get("percentage", 0)
            },
            "performance_metrics": {}
        }
        
        # Add performance metrics if available
        for user_perf in performance_by_user.get("metrics_by_user", []):
            if user_perf.get("user_id") == user_id:
                user_metric["performance_metrics"] = {
                    "average_response_time": user_perf.get("average_response_time", 0),
                    "error_count": user_perf.get("error_count", 0),
                    "error_rate": user_perf.get("error_rate", 0)
                }
                break
        
        user_metrics.append(user_metric)
    
    return {
        "time_period": time_period,
        "total_users": len(user_metrics),
        "total_cost": cost_by_user.get("total_cost", 0),
        "total_tokens": cost_by_user.get("total_tokens", 0),
        "total_interactions": cost_by_user.get("interaction_count", 0),
        "user_metrics": user_metrics
    }

@router.get("/optimization-recommendations")
async def get_optimization_recommendations(
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get AI cost optimization recommendations for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's analytics data"
        )
    
    # Get optimization recommendations
    recommendations = await api_cost_optimization_service.recommend_cost_optimizations(
        organization_id=organization_id
    )
    
    return recommendations

@router.get("/usage-trends")
async def get_usage_trends(
    organization_id: str = Query(..., description="Organization ID"),
    metric_type: str = Query("cost", description="Metric type (cost, tokens, interactions, response_time, errors)"),
    time_range: int = Query(30, description="Number of days to include in the trend"),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get AI usage trends over time for an organization.
    
    This endpoint is restricted to admin users only.
    """
    # Ensure user has access to the organization
    if current_user.organization_id != organization_id and current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this organization's analytics data"
        )
    
    # Validate metric type
    valid_metrics = ["cost", "tokens", "interactions", "response_time", "errors"]
    if metric_type not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric type. Must be one of: {', '.join(valid_metrics)}"
        )
    
    # Get daily data points for the specified time range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=time_range)
    
    # For this example, we'll generate mock trend data
    # In a real implementation, this would query the database for historical metrics
    
    # Generate daily data points
    daily_data = []
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Mock data point based on metric type
        if metric_type == "cost":
            value = 5.0 + (current_date.day % 5) * 2.5  # Mock cost data
        elif metric_type == "tokens":
            value = 10000 + (current_date.day % 10) * 5000  # Mock token data
        elif metric_type == "interactions":
            value = 100 + (current_date.day % 7) * 20  # Mock interaction data
        elif metric_type == "response_time":
            value = 0.5 + (current_date.day % 5) * 0.1  # Mock response time data
        else:  # errors
            value = 2 + (current_date.day % 3)  # Mock error data
        
        daily_data.append({
            "date": date_str,
            "value": value
        })
        
        current_date += timedelta(days=1)
    
    return {
        "organization_id": organization_id,
        "metric_type": metric_type,
        "time_range": time_range,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "trend_data": daily_data
    }
