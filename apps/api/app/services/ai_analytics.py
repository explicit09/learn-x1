from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from prisma.models import AIInteraction, User, Organization
from app.services.prisma import prisma

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAnalyticsService:
    """Service for tracking AI usage metrics and performance."""
    
    async def get_usage_metrics(self, organization_id: str, time_period: str = "week") -> Dict[str, Any]:
        """Get AI usage metrics for an organization.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for metrics (day, week, month)
            
        Returns:
            Dictionary with usage metrics
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
                start_date = now - timedelta(weeks=1)  # Default to week
            
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
                },
                order_by={"created_at": "asc"}
            )
            
            # Calculate metrics
            total_interactions = len(interactions)
            avg_confusion = sum(i.confusion_level or 5 for i in interactions) / max(1, total_interactions)
            
            # Calculate daily usage
            daily_counts = {}
            for interaction in interactions:
                date_str = interaction.created_at.strftime("%Y-%m-%d")
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            
            # Get top users by interaction count
            user_counts = {}
            for interaction in interactions:
                user_counts[interaction.user_id] = user_counts.get(interaction.user_id, 0) + 1
            
            top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_user_ids = [user_id for user_id, _ in top_users]
            
            # Get user details for top users
            top_user_details = await prisma.user.find_many(
                where={"id": {"in": top_user_ids}}
            )
            
            top_users_with_details = [
                {
                    "user_id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "interaction_count": user_counts[user.id]
                }
                for user in top_user_details
            ]
            
            return {
                "total_interactions": total_interactions,
                "average_confusion_level": round(avg_confusion, 2),
                "daily_usage": [{
                    "date": date,
                    "count": count
                } for date, count in daily_counts.items()],
                "top_users": top_users_with_details,
                "time_period": time_period
            }
        except Exception as e:
            logger.error(f"Error getting usage metrics: {str(e)}")
            return {"error": f"Failed to get usage metrics: {str(e)}"}
    
    async def get_performance_metrics(self, organization_id: str, time_period: str = "week") -> Dict[str, Any]:
        """Get AI performance metrics for an organization.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for metrics (day, week, month)
            
        Returns:
            Dictionary with performance metrics
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
                start_date = now - timedelta(weeks=1)  # Default to week
            
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
            
            # Calculate performance metrics
            total_interactions = len(interactions)
            
            # Calculate average response length
            avg_response_length = sum(len(i.response or "") for i in interactions) / max(1, total_interactions)
            
            # Calculate confusion level distribution
            confusion_levels = {}
            for i in range(1, 11):
                confusion_levels[i] = 0
            
            for interaction in interactions:
                level = interaction.confusion_level or 5
                confusion_levels[level] = confusion_levels.get(level, 0) + 1
            
            # Calculate estimated API costs (placeholder - actual implementation would depend on token counting)
            estimated_tokens = sum(len(i.query or "") + len(i.response or "") for i in interactions) / 4  # Rough estimate
            estimated_cost = estimated_tokens / 1000 * 0.002  # Placeholder rate
            
            return {
                "total_interactions": total_interactions,
                "average_response_length": round(avg_response_length, 2),
                "confusion_level_distribution": [{
                    "level": level,
                    "count": count
                } for level, count in confusion_levels.items()],
                "estimated_tokens": int(estimated_tokens),
                "estimated_cost": round(estimated_cost, 2),
                "time_period": time_period
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {"error": f"Failed to get performance metrics: {str(e)}"}
    
    async def log_error(self, error_type: str, error_message: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log an AI service error for monitoring.
        
        Args:
            error_type: Type of error
            error_message: Error message
            user_id: Optional ID of the user who experienced the error
            metadata: Optional additional metadata about the error
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            # Log the error to the database or monitoring system
            # This is a placeholder - actual implementation would depend on your error tracking system
            logger.error(f"AI Error: {error_type} - {error_message} - User: {user_id} - Metadata: {metadata}")
            
            # In a real implementation, you might store this in a database table or send to an error tracking service
            return True
        except Exception as e:
            logger.error(f"Error logging AI error: {str(e)}")
            return False

# Create a singleton instance of the AIAnalyticsService
ai_analytics_service = AIAnalyticsService()
