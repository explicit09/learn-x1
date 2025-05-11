import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
import json

# Import the route handlers directly
from app.api.routes.cost_optimization import get_cost_summary, get_cost_by_user, get_cost_optimization_recommendations, get_recommended_model

# Mock user data for authentication
mock_admin_user = {
    "id": "admin-user-id",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin",
    "organization_id": "org123"
}

mock_super_admin_user = {
    "id": "super-admin-user-id",
    "email": "super.admin@example.com",
    "name": "Super Admin User",
    "role": "super_admin",
    "organization_id": "org456"
}

mock_professor_user = {
    "id": "professor-user-id",
    "email": "professor@example.com",
    "name": "Professor User",
    "role": "professor",
    "organization_id": "org123"
}

# Mock cost summary data
mock_cost_summary = {
    "time_period": "month",
    "total_cost": 150.25,
    "total_tokens": 1500000,
    "interaction_count": 5000,
    "cost_by_type": [
        {
            "interaction_type": "ask",
            "count": 3000,
            "cost": 100.50,
            "tokens": 1000000,
            "percentage": 66.89
        },
        {
            "interaction_type": "quiz",
            "count": 1500,
            "cost": 40.75,
            "tokens": 400000,
            "percentage": 27.12
        },
        {
            "interaction_type": "embedding",
            "count": 500,
            "cost": 9.00,
            "tokens": 100000,
            "percentage": 5.99
        }
    ],
    "cost_by_model": [
        {
            "model": "gpt-4",
            "count": 1000,
            "cost": 90.00,
            "tokens": 500000,
            "percentage": 59.90
        },
        {
            "model": "gpt-3.5-turbo",
            "count": 3500,
            "cost": 51.25,
            "tokens": 900000,
            "percentage": 34.11
        },
        {
            "model": "text-embedding-3-large",
            "count": 500,
            "cost": 9.00,
            "tokens": 100000,
            "percentage": 5.99
        }
    ],
    "average_cost_per_interaction": 0.03
}

# Mock cost by user data
mock_cost_by_user = {
    "time_period": "month",
    "total_cost": 150.25,
    "total_tokens": 1500000,
    "interaction_count": 5000,
    "cost_by_user": [
        {
            "user_id": "user1",
            "user_email": "professor1@example.com",
            "user_name": "Professor One",
            "count": 2500,
            "cost": 80.50,
            "tokens": 800000,
            "percentage": 53.58
        },
        {
            "user_id": "user2",
            "user_email": "student1@example.com",
            "user_name": "Student One",
            "count": 1500,
            "cost": 45.75,
            "tokens": 500000,
            "percentage": 30.45
        },
        {
            "user_id": "user3",
            "user_email": "admin@example.com",
            "user_name": "Admin User",
            "count": 1000,
            "cost": 24.00,
            "tokens": 200000,
            "percentage": 15.97
        }
    ],
    "average_cost_per_user": 50.08
}

# Mock recommendations data
mock_recommendations = {
    "total_current_cost": 150.25,
    "estimated_savings": 45.75,
    "estimated_optimized_cost": 104.50,
    "savings_percentage": 30.45,
    "recommendations": [
        {
            "recommendation": "Switch from gpt-4 to gpt-4-turbo for most operations",
            "current_model": "gpt-4",
            "recommended_model": "gpt-4-turbo",
            "current_cost": 90.00,
            "estimated_new_cost": 45.00,
            "estimated_savings": 45.00,
            "impact": "medium",
            "implementation_difficulty": "low"
        },
        {
            "recommendation": "Implement caching for embedding operations",
            "interaction_type": "embedding",
            "current_cost": 9.00,
            "estimated_new_cost": 5.40,
            "estimated_savings": 3.60,
            "impact": "medium",
            "implementation_difficulty": "medium"
        },
        {
            "recommendation": "Implement tiered access to AI features based on user roles",
            "estimated_savings": "Variable",
            "impact": "high",
            "implementation_difficulty": "medium"
        }
    ]
}

# Setup authentication mocks
def mock_get_current_admin_user():
    return mock_admin_user

def mock_get_current_super_admin_user():
    return mock_super_admin_user

def mock_get_current_professor_user():
    return mock_professor_user

# Test cases
@pytest.mark.asyncio
@patch("app.api.routes.cost_optimization.get_current_admin_user")
@patch("app.api.routes.cost_optimization.api_cost_optimization_service.get_cost_summary")
async def test_get_cost_summary(mock_get_cost_summary, mock_get_admin_user):
    # Setup mocks
    mock_get_admin_user.return_value = mock_admin_user
    mock_get_cost_summary.return_value = mock_cost_summary
    
    # Test the endpoint
    result = await get_cost_summary(
        organization_id="org123",
        time_period="month",
        current_user=mock_admin_user
    )
    
    # Verify the response
    assert result["total_cost"] == 150.25
    assert result["total_tokens"] == 1500000
    assert result["interaction_count"] == 5000
    assert len(result["cost_by_type"]) == 3
    assert len(result["cost_by_model"]) == 3

@pytest.mark.asyncio
@patch("app.api.routes.cost_optimization.get_current_admin_user")
@patch("app.api.routes.cost_optimization.api_cost_optimization_service.get_cost_by_user")
async def test_get_cost_by_user(mock_get_cost_by_user, mock_get_admin_user):
    # Setup mocks
    mock_get_admin_user.return_value = mock_admin_user
    mock_get_cost_by_user.return_value = mock_cost_by_user
    
    # Test the endpoint
    result = await get_cost_by_user(
        organization_id="org123",
        time_period="month",
        current_user=mock_admin_user
    )
    
    # Verify the response
    assert result["total_cost"] == 150.25
    assert result["total_tokens"] == 1500000
    assert result["interaction_count"] == 5000
    assert len(result["cost_by_user"]) == 3

@pytest.mark.asyncio
@patch("app.api.routes.cost_optimization.get_current_admin_user")
@patch("app.api.routes.cost_optimization.api_cost_optimization_service.recommend_cost_optimizations")
async def test_get_cost_optimization_recommendations(mock_recommend_cost_optimizations, mock_get_admin_user):
    # Setup mocks
    mock_get_admin_user.return_value = mock_admin_user
    mock_recommend_cost_optimizations.return_value = mock_recommendations
    
    # Test the endpoint
    result = await get_cost_optimization_recommendations(
        organization_id="org123",
        current_user=mock_admin_user
    )
    
    # Verify the response
    assert result["total_current_cost"] == 150.25
    assert result["estimated_savings"] == 45.75
    assert result["estimated_optimized_cost"] == 104.50
    assert result["savings_percentage"] == 30.45
    assert len(result["recommendations"]) == 3

@pytest.mark.asyncio
@patch("app.api.routes.cost_optimization.get_current_user")
@patch("app.api.routes.cost_optimization.api_cost_optimization_service.get_recommended_model")
async def test_get_recommended_model(mock_get_recommended_model, mock_get_current_user):
    # Setup mocks
    mock_get_current_user.return_value = mock_professor_user
    mock_get_recommended_model.return_value = "gpt-3.5-turbo"
    
    # Test the endpoint
    result = await get_recommended_model(
        interaction_type="completion",
        user_role="professor",
        content_complexity=None,
        current_user=mock_professor_user
    )
    
    # Verify the response
    assert result["recommended_model"] == "gpt-3.5-turbo"

@pytest.mark.asyncio
@patch("app.api.routes.cost_optimization.get_current_admin_user")
async def test_get_cost_summary_unauthorized_org(mock_get_admin_user):
    # Setup mocks - admin user from different organization
    mock_get_admin_user.return_value = mock_admin_user
    
    # Test the endpoint with a different organization ID
    with pytest.raises(HTTPException) as excinfo:
        await get_cost_summary(
            organization_id="org456",
            time_period="month",
            current_user=mock_admin_user
        )
    
    # Verify the exception - should be forbidden
    assert excinfo.value.status_code == 403
    assert "permission" in excinfo.value.detail

@pytest.mark.asyncio
@patch("app.api.routes.cost_optimization.get_current_admin_user")
@patch("app.api.routes.cost_optimization.api_cost_optimization_service.get_cost_summary")
async def test_get_cost_summary_super_admin_access(mock_get_cost_summary, mock_get_admin_user):
    # Setup mocks - super admin user can access any organization
    mock_get_admin_user.return_value = mock_super_admin_user
    mock_get_cost_summary.return_value = mock_cost_summary
    
    # Test the endpoint with a different organization ID
    result = await get_cost_summary(
        organization_id="org123",
        time_period="month",
        current_user=mock_super_admin_user
    )
    
    # Verify the response - super admin should have access
    assert result["total_cost"] == 150.25
    assert result["total_tokens"] == 1500000

@pytest.mark.asyncio
@patch("app.api.routes.cost_optimization.get_current_admin_user")
async def test_get_cost_summary_invalid_time_period(mock_get_admin_user):
    # Setup mocks
    mock_get_admin_user.return_value = mock_admin_user
    
    # Test the endpoint with an invalid time period
    with pytest.raises(HTTPException) as excinfo:
        await get_cost_summary(
            organization_id="org123",
            time_period="invalid",
            current_user=mock_admin_user
        )
    
    # Verify the exception - should be bad request
    assert excinfo.value.status_code == 400
    assert "Invalid time period" in excinfo.value.detail
