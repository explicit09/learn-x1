import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.analytics import (
    get_response_time_metrics,
    get_error_rate_metrics,
    get_token_usage_metrics,
    get_api_usage_summary,
    get_api_usage_by_user
)

# Setup test client
client = TestClient(app)

# Mock user data
@pytest.fixture
def admin_user():
    return MagicMock(
        id="admin1",
        email="admin@example.com",
        organization_id="org123",
        role="admin"
    )

@pytest.fixture
def super_admin_user():
    return MagicMock(
        id="superadmin1",
        email="superadmin@example.com",
        organization_id="org456",
        role="super_admin"
    )

@pytest.fixture
def regular_user():
    return MagicMock(
        id="user1",
        email="user@example.com",
        organization_id="org123",
        role="student"
    )

# Mock dependencies
@pytest.fixture
def mock_performance_monitoring():
    with patch('app.api.routes.analytics.performance_monitoring_service') as mock:
        yield mock

@pytest.fixture
def mock_api_usage():
    with patch('app.api.routes.analytics.api_usage_service') as mock:
        yield mock

# Test response time metrics endpoint
@pytest.mark.asyncio
async def test_get_response_time_metrics(admin_user, mock_performance_monitoring):
    # Mock the performance monitoring service response
    mock_performance_monitoring.get_response_time_metrics.return_value = {
        "time_period": "day",
        "count": 100,
        "average_ms": 150.5,
        "median_ms": 120.0,
        "min_ms": 50.0,
        "max_ms": 500.0,
        "p95_ms": 300.0,
        "p99_ms": 450.0
    }
    
    # Test with admin user accessing their own organization
    result = await get_response_time_metrics(
        organization_id=admin_user.organization_id,
        time_period="day",
        current_user=admin_user
    )
    
    # Verify the result
    assert result["count"] == 100
    assert result["average_ms"] == 150.5
    
    # Verify the service was called with correct parameters
    mock_performance_monitoring.get_response_time_metrics.assert_called_with(
        organization_id=admin_user.organization_id,
        time_period="day"
    )

@pytest.mark.asyncio
async def test_get_response_time_metrics_permission_denied(admin_user):
    # Test with admin user trying to access another organization
    with pytest.raises(HTTPException) as excinfo:
        await get_response_time_metrics(
            organization_id="different_org",
            time_period="day",
            current_user=admin_user
        )
    
    # Verify the exception
    assert excinfo.value.status_code == 403
    assert "permission" in excinfo.value.detail.lower()

@pytest.mark.asyncio
async def test_get_response_time_metrics_super_admin(super_admin_user, mock_performance_monitoring):
    # Mock the performance monitoring service response
    mock_performance_monitoring.get_response_time_metrics.return_value = {
        "time_period": "day",
        "count": 100,
        "average_ms": 150.5
    }
    
    # Test with super admin accessing any organization
    result = await get_response_time_metrics(
        organization_id="any_org",
        time_period="day",
        current_user=super_admin_user
    )
    
    # Verify the result
    assert result["count"] == 100
    assert result["average_ms"] == 150.5

@pytest.mark.asyncio
async def test_get_response_time_metrics_invalid_time_period(admin_user):
    # Test with invalid time period
    with pytest.raises(HTTPException) as excinfo:
        await get_response_time_metrics(
            organization_id=admin_user.organization_id,
            time_period="invalid",
            current_user=admin_user
        )
    
    # Verify the exception
    assert excinfo.value.status_code == 400
    assert "invalid time period" in excinfo.value.detail.lower()

@pytest.mark.asyncio
async def test_get_response_time_metrics_service_error(admin_user, mock_performance_monitoring):
    # Mock the performance monitoring service error response
    mock_performance_monitoring.get_response_time_metrics.return_value = {
        "error": "No users found in organization"
    }
    
    # Test with service returning an error
    with pytest.raises(HTTPException) as excinfo:
        await get_response_time_metrics(
            organization_id=admin_user.organization_id,
            time_period="day",
            current_user=admin_user
        )
    
    # Verify the exception
    assert excinfo.value.status_code == 400
    assert "no users found" in excinfo.value.detail.lower()

# Test error rate metrics endpoint
@pytest.mark.asyncio
async def test_get_error_rate_metrics(admin_user, mock_performance_monitoring):
    # Mock the performance monitoring service response
    mock_performance_monitoring.get_error_rate_metrics.return_value = {
        "time_period": "day",
        "total_interactions": 1000,
        "error_interactions": 50,
        "error_rate": 5.0,
        "success_rate": 95.0
    }
    
    # Test with admin user accessing their own organization
    result = await get_error_rate_metrics(
        organization_id=admin_user.organization_id,
        time_period="day",
        current_user=admin_user
    )
    
    # Verify the result
    assert result["total_interactions"] == 1000
    assert result["error_rate"] == 5.0
    assert result["success_rate"] == 95.0
    
    # Verify the service was called with correct parameters
    mock_performance_monitoring.get_error_rate_metrics.assert_called_with(
        organization_id=admin_user.organization_id,
        time_period="day"
    )

# Test token usage metrics endpoint
@pytest.mark.asyncio
async def test_get_token_usage_metrics(admin_user, mock_performance_monitoring):
    # Mock the performance monitoring service response
    mock_performance_monitoring.get_token_usage_metrics.return_value = {
        "time_period": "day",
        "total_interactions": 500,
        "total_tokens": 100000,
        "avg_tokens_per_interaction": 200.0,
        "token_usage_by_type": [
            {
                "interaction_type": "ask",
                "count": 300,
                "total_tokens": 60000,
                "avg_tokens": 200.0
            },
            {
                "interaction_type": "quiz",
                "count": 200,
                "total_tokens": 40000,
                "avg_tokens": 200.0
            }
        ]
    }
    
    # Test with admin user accessing their own organization
    result = await get_token_usage_metrics(
        organization_id=admin_user.organization_id,
        time_period="day",
        current_user=admin_user
    )
    
    # Verify the result
    assert result["total_interactions"] == 500
    assert result["total_tokens"] == 100000
    assert result["avg_tokens_per_interaction"] == 200.0
    assert len(result["token_usage_by_type"]) == 2
    
    # Verify the service was called with correct parameters
    mock_performance_monitoring.get_token_usage_metrics.assert_called_with(
        organization_id=admin_user.organization_id,
        time_period="day"
    )

# Test API usage summary endpoint
@pytest.mark.asyncio
async def test_get_api_usage_summary(admin_user, mock_api_usage):
    # Mock the API usage service response
    mock_api_usage.get_usage_summary.return_value = {
        "time_period": "day",
        "total_calls": 2000,
        "unique_users": 50,
        "calls_by_endpoint": {
            "/ai/ask": 1000,
            "/ai/quiz": 800,
            "/ai/explain": 200
        }
    }
    
    # Test with admin user accessing their own organization
    result = await get_api_usage_summary(
        organization_id=admin_user.organization_id,
        time_period="day",
        current_user=admin_user
    )
    
    # Verify the result
    assert result["total_calls"] == 2000
    assert result["unique_users"] == 50
    assert result["calls_by_endpoint"]["/ai/ask"] == 1000
    
    # Verify the service was called with correct parameters
    mock_api_usage.get_usage_summary.assert_called_with(
        organization_id=admin_user.organization_id,
        time_period="day"
    )

# Test API usage by user endpoint
@pytest.mark.asyncio
async def test_get_api_usage_by_user(admin_user, mock_api_usage):
    # Mock the API usage service response
    mock_api_usage.get_usage_by_user.return_value = {
        "time_period": "day",
        "total_calls": 2000,
        "usage_by_user": [
            {
                "user_id": "user1",
                "user_email": "user1@example.com",
                "total_calls": 800,
                "percentage": 40.0
            },
            {
                "user_id": "user2",
                "user_email": "user2@example.com",
                "total_calls": 600,
                "percentage": 30.0
            },
            {
                "user_id": "user3",
                "user_email": "user3@example.com",
                "total_calls": 600,
                "percentage": 30.0
            }
        ]
    }
    
    # Test with admin user accessing their own organization
    result = await get_api_usage_by_user(
        organization_id=admin_user.organization_id,
        time_period="day",
        current_user=admin_user
    )
    
    # Verify the result
    assert result["total_calls"] == 2000
    assert len(result["usage_by_user"]) == 3
    assert result["usage_by_user"][0]["total_calls"] == 800
    
    # Verify the service was called with correct parameters
    mock_api_usage.get_usage_by_user.assert_called_with(
        organization_id=admin_user.organization_id,
        time_period="day"
    )
