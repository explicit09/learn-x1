from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from datetime import datetime, timedelta
import json
import statistics
from app.services.prisma import prisma
from app.core.config import settings

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from prisma.models import AIInteraction, User, Organization

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMonitoringService:
    """Service for monitoring AI performance metrics."""
    
    async def log_performance_metric(self, metric_name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log a performance metric for monitoring.
        
        Args:
            metric_name: Name of the metric (e.g., 'response_time', 'token_count')
            value: Value of the metric
            metadata: Optional additional metadata about the metric
            
        Returns:
            True if logging was successful, False otherwise
        """
        try:
            # In a real implementation, you would have a dedicated table for metrics
            # For now, we'll use a simple logging approach
            logger.info(f"Performance metric: {metric_name}={value}, metadata={metadata}")
            
            # You could also store metrics in a time-series database or monitoring service
            # For this implementation, we'll return success
            return True
        except Exception as e:
            logger.error(f"Error logging performance metric: {str(e)}")
            return False
    
    async def get_response_time_metrics(self, organization_id: str, time_period: str = "day") -> Dict[str, Any]:
        """Get response time metrics for AI interactions.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for metrics (day, week, month)
            
        Returns:
            Dictionary with response time metrics
        """
        try:
            # Calculate date range based on time period
            now = datetime.utcnow()
            if time_period == "day":
                start_date = now - timedelta(days=1)
            elif time_period == "week":
                start_date = now - timedelta(weeks=1)
            elif time_period == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)  # Default to day
            
            # Get all users in the organization
            users = await prisma.user.find_many(
                where={"organization_id": organization_id}
            )
            user_ids = [user.id for user in users]
            
            if not user_ids:
                return {"error": "No users found in organization"}
            
            # Get AI interactions for these users in the time period
            interactions = await prisma.aiinteraction.find_many(
                where={
                    "user_id": {"in": user_ids},
                    "created_at": {"gte": start_date}
                }
            )
            
            # Extract response times from metadata
            response_times = []
            for interaction in interactions:
                metadata = interaction.metadata or {}
                if "response_time_ms" in metadata:
                    response_times.append(metadata["response_time_ms"])
            
            if not response_times:
                return {
                    "time_period": time_period,
                    "count": 0,
                    "message": "No response time data available"
                }
            
            # Calculate metrics
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
            
            return {
                "time_period": time_period,
                "count": len(response_times),
                "average_ms": round(avg_response_time, 2),
                "median_ms": round(median_response_time, 2),
                "min_ms": round(min_response_time, 2),
                "max_ms": round(max_response_time, 2),
                "p95_ms": round(p95_response_time, 2),
                "p99_ms": round(p99_response_time, 2)
            }
        except Exception as e:
            logger.error(f"Error getting response time metrics: {str(e)}")
            return {"error": f"Failed to get response time metrics: {str(e)}"}
    
    async def get_error_rate_metrics(self, organization_id: str, time_period: str = "day") -> Dict[str, Any]:
        """Get error rate metrics for AI interactions.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for metrics (day, week, month)
            
        Returns:
            Dictionary with error rate metrics
        """
        try:
            # Calculate date range based on time period
            now = datetime.utcnow()
            if time_period == "day":
                start_date = now - timedelta(days=1)
            elif time_period == "week":
                start_date = now - timedelta(weeks=1)
            elif time_period == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)  # Default to day
            
            # Get all users in the organization
            users = await prisma.user.find_many(
                where={"organization_id": organization_id}
            )
            user_ids = [user.id for user in users]
            
            if not user_ids:
                return {"error": "No users found in organization"}
            
            # Get total AI interactions for these users in the time period
            total_interactions = await prisma.aiinteraction.count(
                where={
                    "user_id": {"in": user_ids},
                    "created_at": {"gte": start_date}
                }
            )
            
            # Get error interactions
            error_interactions = await prisma.aiinteraction.count(
                where={
                    "user_id": {"in": user_ids},
                    "created_at": {"gte": start_date},
                    "metadata": {"path": ["error"], "not": None}
                }
            )
            
            if total_interactions == 0:
                return {
                    "time_period": time_period,
                    "total_interactions": 0,
                    "error_rate": 0,
                    "message": "No interactions in the specified time period"
                }
            
            # Calculate error rate
            error_rate = (error_interactions / total_interactions) * 100
            
            return {
                "time_period": time_period,
                "total_interactions": total_interactions,
                "error_interactions": error_interactions,
                "error_rate": round(error_rate, 2),
                "success_rate": round(100 - error_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error getting error rate metrics: {str(e)}")
            return {"error": f"Failed to get error rate metrics: {str(e)}"}
    
    async def get_token_usage_metrics(self, organization_id: str, time_period: str = "day") -> Dict[str, Any]:
        """Get token usage metrics for AI interactions.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for metrics (day, week, month)
            
        Returns:
            Dictionary with token usage metrics
        """
        try:
            # Calculate date range based on time period
            now = datetime.utcnow()
            if time_period == "day":
                start_date = now - timedelta(days=1)
            elif time_period == "week":
                start_date = now - timedelta(weeks=1)
            elif time_period == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)  # Default to day
            
            # Get all users in the organization
            users = await prisma.user.find_many(
                where={"organization_id": organization_id}
            )
            user_ids = [user.id for user in users]
            
            if not user_ids:
                return {"error": "No users found in organization"}
            
            # Get AI interactions for these users in the time period
            interactions = await prisma.aiinteraction.find_many(
                where={
                    "user_id": {"in": user_ids},
                    "created_at": {"gte": start_date}
                }
            )
            
            if not interactions:
                return {
                    "time_period": time_period,
                    "total_interactions": 0,
                    "message": "No interactions in the specified time period"
                }
            
            # Calculate token usage metrics
            total_tokens = sum(i.tokens_used or 0 for i in interactions)
            avg_tokens_per_interaction = total_tokens / len(interactions)
            
            # Group by interaction type
            token_usage_by_type = {}
            for interaction in interactions:
                interaction_type = interaction.interaction_type or "unknown"
                tokens = interaction.tokens_used or 0
                
                if interaction_type not in token_usage_by_type:
                    token_usage_by_type[interaction_type] = {
                        "count": 0,
                        "tokens": 0
                    }
                
                token_usage_by_type[interaction_type]["count"] += 1
                token_usage_by_type[interaction_type]["tokens"] += tokens
            
            # Format token usage by type for response
            token_usage_list = [
                {
                    "interaction_type": interaction_type,
                    "count": data["count"],
                    "total_tokens": data["tokens"],
                    "avg_tokens": round(data["tokens"] / data["count"], 2) if data["count"] > 0 else 0
                }
                for interaction_type, data in token_usage_by_type.items()
            ]
            
            # Sort by total tokens (highest first)
            token_usage_list.sort(key=lambda x: x["total_tokens"], reverse=True)
            
            return {
                "time_period": time_period,
                "total_interactions": len(interactions),
                "total_tokens": total_tokens,
                "avg_tokens_per_interaction": round(avg_tokens_per_interaction, 2),
                "token_usage_by_type": token_usage_list
            }
        except Exception as e:
            logger.error(f"Error getting token usage metrics: {str(e)}")
            return {"error": f"Failed to get token usage metrics: {str(e)}"}
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate the percentile of a list of values.
        
        Args:
            data: List of values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not data:
            return 0
        
        # Sort the data
        sorted_data = sorted(data)
        
        # Calculate the index
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_data):
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
        else:
            return sorted_data[f]

# Create a singleton instance of the PerformanceMonitoringService
performance_monitoring_service = PerformanceMonitoringService()
