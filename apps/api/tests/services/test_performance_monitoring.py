import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import statistics

# Mock the prisma module before importing the service
with patch('app.services.prisma.Prisma') as mock_prisma_class:
    mock_prisma_instance = AsyncMock()
    mock_prisma_class.return_value = mock_prisma_instance
    with patch('app.services.prisma.prisma', mock_prisma_instance):
        from app.services.performance_monitoring import PerformanceMonitoringService

@pytest.fixture
def performance_service():
    return PerformanceMonitoringService()

@pytest.fixture
def mock_prisma():
    # The prisma module is already mocked at the module level
    # Just return the mock instance for test functions to use
    return mock_prisma_instance

@pytest.mark.asyncio
async def test_log_performance_metric(performance_service):
    # Test successful logging
    with patch('app.services.performance_monitoring.logger') as mock_logger:
        result = await performance_service.log_performance_metric(
            metric_name="response_time", 
            value=150.5, 
            metadata={"endpoint": "/ai/ask", "model": "gpt-4"}
        )
        
        assert result is True
        mock_logger.info.assert_called_once()

    # Test exception handling
    with patch('app.services.performance_monitoring.logger') as mock_logger:
        mock_logger.info.side_effect = Exception("Test exception")
        result = await performance_service.log_performance_metric(
            metric_name="response_time", 
            value=150.5
        )
        
        assert result is False
        mock_logger.error.assert_called_once()

@pytest.mark.asyncio
async def test_get_response_time_metrics(performance_service, mock_prisma):
    # Setup test data
    org_id = "org123"
    user1 = MagicMock(id="user1")
    user2 = MagicMock(id="user2")
    
    # Mock users query
    mock_prisma.user.find_many.return_value = [user1, user2]
    
    # Mock interactions with response time data
    interaction1 = MagicMock(
        metadata={"response_time_ms": 100}
    )
    interaction2 = MagicMock(
        metadata={"response_time_ms": 200}
    )
    interaction3 = MagicMock(
        metadata={"response_time_ms": 300}
    )
    
    mock_prisma.aiinteraction.find_many.return_value = [interaction1, interaction2, interaction3]
    
    # Test with day time period
    result = await performance_service.get_response_time_metrics(org_id, "day")
    
    # Verify results
    assert result["count"] == 3
    assert result["average_ms"] == 200.0  # (100 + 200 + 300) / 3
    assert result["median_ms"] == 200.0
    assert result["min_ms"] == 100.0
    assert result["max_ms"] == 300.0
    
    # Verify correct query parameters
    mock_prisma.user.find_many.assert_called_with(
        where={"organization_id": org_id}
    )
    
    # Test with no users
    mock_prisma.user.find_many.return_value = []
    result = await performance_service.get_response_time_metrics(org_id, "day")
    assert "error" in result
    
    # Test with no interactions
    mock_prisma.user.find_many.return_value = [user1, user2]
    mock_prisma.aiinteraction.find_many.return_value = []
    result = await performance_service.get_response_time_metrics(org_id, "day")
    assert result["count"] == 0
    assert "message" in result

@pytest.mark.asyncio
async def test_get_error_rate_metrics(performance_service, mock_prisma):
    # Setup test data
    org_id = "org123"
    user1 = MagicMock(id="user1")
    user2 = MagicMock(id="user2")
    
    # Mock users query
    mock_prisma.user.find_many.return_value = [user1, user2]
    
    # Mock interaction counts
    mock_prisma.aiinteraction.count.side_effect = [100, 15]  # Total: 100, Errors: 15
    
    # Test with day time period
    result = await performance_service.get_error_rate_metrics(org_id, "day")
    
    # Verify results
    assert result["total_interactions"] == 100
    assert result["error_interactions"] == 15
    assert result["error_rate"] == 15.0  # (15 / 100) * 100
    assert result["success_rate"] == 85.0  # 100 - 15.0
    
    # Test with no users
    mock_prisma.user.find_many.return_value = []
    result = await performance_service.get_error_rate_metrics(org_id, "day")
    assert "error" in result
    
    # Test with no interactions
    mock_prisma.user.find_many.return_value = [user1, user2]
    mock_prisma.aiinteraction.count.side_effect = [0, 0]  # Total: 0, Errors: 0
    result = await performance_service.get_error_rate_metrics(org_id, "day")
    assert result["total_interactions"] == 0
    assert result["error_rate"] == 0
    assert "message" in result

@pytest.mark.asyncio
async def test_get_token_usage_metrics(performance_service, mock_prisma):
    # Setup test data
    org_id = "org123"
    user1 = MagicMock(id="user1")
    user2 = MagicMock(id="user2")
    
    # Mock users query
    mock_prisma.user.find_many.return_value = [user1, user2]
    
    # Mock interactions with token usage data
    interaction1 = MagicMock(
        tokens_used=100,
        interaction_type="ask"
    )
    interaction2 = MagicMock(
        tokens_used=200,
        interaction_type="ask"
    )
    interaction3 = MagicMock(
        tokens_used=300,
        interaction_type="quiz"
    )
    
    mock_prisma.aiinteraction.find_many.return_value = [interaction1, interaction2, interaction3]
    
    # Test with day time period
    result = await performance_service.get_token_usage_metrics(org_id, "day")
    
    # Verify results
    assert result["total_interactions"] == 3
    assert result["total_tokens"] == 600  # 100 + 200 + 300
    assert result["avg_tokens_per_interaction"] == 200.0  # 600 / 3
    
    # Check token usage by type
    token_usage = result["token_usage_by_type"]
    assert len(token_usage) == 2  # Two types: "ask" and "quiz"
    
    # Find the "ask" type in the results
    ask_usage = next((item for item in token_usage if item["interaction_type"] == "ask"), None)
    assert ask_usage is not None
    assert ask_usage["count"] == 2
    assert ask_usage["total_tokens"] == 300  # 100 + 200
    assert ask_usage["avg_tokens"] == 150.0  # 300 / 2
    
    # Find the "quiz" type in the results
    quiz_usage = next((item for item in token_usage if item["interaction_type"] == "quiz"), None)
    assert quiz_usage is not None
    assert quiz_usage["count"] == 1
    assert quiz_usage["total_tokens"] == 300
    assert quiz_usage["avg_tokens"] == 300.0  # 300 / 1
    
    # Test with no users
    mock_prisma.user.find_many.return_value = []
    result = await performance_service.get_token_usage_metrics(org_id, "day")
    assert "error" in result
    
    # Test with no interactions
    mock_prisma.user.find_many.return_value = [user1, user2]
    mock_prisma.aiinteraction.find_many.return_value = []
    result = await performance_service.get_token_usage_metrics(org_id, "day")
    assert result["total_interactions"] == 0
    assert "message" in result

@pytest.mark.asyncio
async def test_percentile_calculation(performance_service):
    # Test with empty list
    result = performance_service._percentile([], 95)
    assert result == 0
    
    # Test with single value
    result = performance_service._percentile([100], 95)
    assert result == 100
    
    # Test with multiple values
    data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    
    # 50th percentile should be the median
    result = performance_service._percentile(data, 50)
    assert result == 55.0  # Median of the data
    
    # 95th percentile
    result = performance_service._percentile(data, 95)
    assert result == 95.5  # Expected 95th percentile value
    
    # 100th percentile should be the maximum
    result = performance_service._percentile(data, 100)
    assert result == 100  # Maximum value
