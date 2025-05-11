# AI Analytics and Monitoring

## Overview

The AI Analytics and Monitoring system provides comprehensive tracking, analysis, and optimization of AI usage within the LEARN-X platform. This documentation covers the key components, APIs, and usage patterns for monitoring AI performance, tracking costs, and optimizing API usage.

## Key Components

### 1. Performance Monitoring Service

The Performance Monitoring Service tracks and analyzes AI component performance metrics including:

- Response times (average, p90, p95, p99)
- Error rates and error types
- Token usage by model and interaction type
- User-specific performance metrics

**Key Methods:**
- `log_performance_metric()` - Records individual performance metrics
- `get_response_time_metrics()` - Retrieves response time statistics
- `get_error_rates()` - Retrieves error rate statistics
- `get_metrics_by_user()` - Retrieves user-specific performance metrics

### 2. API Cost Optimization Service

The API Cost Optimization Service tracks and analyzes API usage costs, providing insights and recommendations for cost optimization:

- Cost tracking by model, interaction type, and user
- Cost forecasting and trend analysis
- Optimization recommendations based on usage patterns
- Model selection guidance based on user roles and content complexity

**Key Methods:**
- `calculate_cost()` - Calculates cost for specific API calls
- `log_api_cost()` - Records API usage costs
- `get_cost_summary()` - Retrieves cost summaries by various dimensions
- `get_cost_by_user()` - Retrieves user-specific cost metrics
- `recommend_cost_optimizations()` - Generates cost-saving recommendations
- `get_recommended_model()` - Suggests optimal models based on context

### 3. AI Analytics Dashboard API

The AI Analytics Dashboard API provides endpoints for accessing comprehensive analytics data:

- Combined performance and cost metrics
- User-specific analytics
- Optimization recommendations
- Usage trends over time

**Key Endpoints:**
- `/api/ai-analytics-dashboard/summary` - Comprehensive analytics summary
- `/api/ai-analytics-dashboard/user-metrics` - User-specific analytics
- `/api/ai-analytics-dashboard/optimization-recommendations` - Cost optimization recommendations
- `/api/ai-analytics-dashboard/usage-trends` - Usage trends over time

### 4. Cost Optimization API

The Cost Optimization API provides direct access to cost optimization features:

- Cost summaries by various dimensions
- User-specific cost breakdowns
- Optimization recommendations
- Model selection guidance

**Key Endpoints:**
- `/api/cost-optimization/summary` - Cost summary by model and interaction type
- `/api/cost-optimization/by-user` - Cost breakdown by user
- `/api/cost-optimization/recommendations` - Cost optimization recommendations
- `/api/cost-optimization/recommended-model` - Model selection guidance

## Usage Examples

### Tracking Performance Metrics

```python
# Log a performance metric
await performance_monitoring_service.log_performance_metric(
    metric_name="response_time",
    value=0.85,  # seconds
    metadata={
        "model": "gpt-4",
        "interaction_type": "ask",
        "user_id": "user123",
        "organization_id": "org456"
    }
)

# Get response time metrics
metrics = await performance_monitoring_service.get_response_time_metrics(
    organization_id="org456",
    time_period="month"
)
```

### Tracking API Costs

```python
# Log API usage cost
await api_cost_optimization_service.log_api_cost(
    organization_id="org456",
    user_id="user123",
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    interaction_type="ask",
    metadata={
        "course_id": "course789",
        "material_id": "material012"
    }
)

# Get cost summary
cost_summary = await api_cost_optimization_service.get_cost_summary(
    organization_id="org456",
    time_period="month"
)
```

### Getting Optimization Recommendations

```python
# Get cost optimization recommendations
recommendations = await api_cost_optimization_service.recommend_cost_optimizations(
    organization_id="org456"
)

# Get recommended model for specific context
recommended_model = await api_cost_optimization_service.get_recommended_model(
    interaction_type="completion",
    user_role="professor",
    content_complexity="high"
)
```

## Security and Access Control

All analytics and monitoring endpoints are protected by role-based access control:

- Cost and performance data is isolated by organization
- Only admin users can access analytics data for their organization
- Super admin users can access analytics data for any organization
- Model recommendation endpoints are available to all authenticated users

## Database Schema

The analytics and monitoring system uses the following database tables:

- `performance_metrics` - Stores individual performance measurements
- `api_usage_costs` - Stores API usage cost data
- `error_logs` - Stores detailed error information
- `optimization_recommendations` - Stores generated optimization recommendations

## Environment Configuration

The following environment variables can be used to configure the analytics and monitoring system:

- `ENABLE_AI_ANALYTICS` - Enable/disable analytics tracking (default: true)
- `ANALYTICS_RETENTION_DAYS` - Number of days to retain detailed analytics data (default: 90)
- `COST_OPTIMIZATION_THRESHOLD` - Minimum cost threshold for generating recommendations (default: 10.0)

## Testing

The analytics and monitoring components include comprehensive tests:

- Unit tests for individual services
- Integration tests for API endpoints
- Mock services for testing without dependencies

Run tests using:

```bash
python -m pytest tests/services/test_performance_monitoring.py
python -m pytest tests/services/test_api_cost_optimization_basic.py
python -m pytest tests/services/test_ai_analytics_dashboard_basic.py
```

## Future Enhancements

Planned enhancements for the analytics and monitoring system include:

- Real-time analytics dashboard with WebSocket updates
- Anomaly detection for unusual usage patterns
- Automated cost optimization actions based on recommendations
- Enhanced visualization components for the frontend
- Integration with external monitoring and alerting systems
