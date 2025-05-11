from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import json
from prisma.models import AIInteraction, User, Organization
from app.services.prisma import prisma
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIUsageService:
    """Service for tracking and managing API usage."""
    
    async def track_api_call(self, user_id: str, api_name: str, tokens_used: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Track an API call for usage monitoring.
        
        Args:
            user_id: ID of the user making the API call
            api_name: Name of the API being called (e.g., 'openai.completion', 'openai.embedding')
            tokens_used: Number of tokens used in the API call
            metadata: Optional additional metadata about the API call
            
        Returns:
            True if tracking was successful, False otherwise
        """
        try:
            # Get user organization
            user = await prisma.user.find_unique(
                where={"id": user_id}
            )
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Calculate estimated cost based on token usage and API
            cost = self._calculate_cost(api_name, tokens_used)
            
            # Store API usage in database
            # Note: In a real implementation, you would have a dedicated table for API usage
            # For now, we'll use the AIInteraction table with a specific interaction_type
            await prisma.aiinteraction.create(
                data={
                    "user_id": user_id,
                    "query": f"API Call: {api_name}",
                    "response": "",  # No response for API tracking
                    "tokens_used": tokens_used,
                    "interaction_type": "api_usage",
                    "metadata": {
                        "api_name": api_name,
                        "tokens_used": tokens_used,
                        "cost": cost,
                        "timestamp": datetime.utcnow().isoformat(),
                        **(metadata or {})
                    }
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Error tracking API call: {str(e)}")
            return False
    
    async def get_usage_summary(self, organization_id: str, time_period: str = "month") -> Dict[str, Any]:
        """Get API usage summary for an organization.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for the summary (day, week, month, year)
            
        Returns:
            Dictionary with usage summary
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
            elif time_period == "year":
                start_date = now - timedelta(days=365)
            else:
                start_date = now - timedelta(days=30)  # Default to month
            
            # Get all users in the organization
            users = await prisma.user.find_many(
                where={"organization_id": organization_id}
            )
            user_ids = [user.id for user in users]
            
            if not user_ids:
                return {"error": "No users found in organization"}
            
            # Get API usage interactions for these users in the time period
            interactions = await prisma.aiinteraction.find_many(
                where={
                    "user_id": {"in": user_ids},
                    "created_at": {"gte": start_date},
                    "interaction_type": "api_usage"
                }
            )
            
            # Calculate usage metrics
            total_calls = len(interactions)
            total_tokens = sum(i.tokens_used or 0 for i in interactions)
            
            # Group by API name
            api_usage = {}
            for interaction in interactions:
                metadata = interaction.metadata or {}
                api_name = metadata.get("api_name", "unknown")
                tokens = interaction.tokens_used or 0
                cost = metadata.get("cost", 0)
                
                if api_name not in api_usage:
                    api_usage[api_name] = {
                        "calls": 0,
                        "tokens": 0,
                        "cost": 0
                    }
                
                api_usage[api_name]["calls"] += 1
                api_usage[api_name]["tokens"] += tokens
                api_usage[api_name]["cost"] += cost
            
            # Calculate total cost
            total_cost = sum(api["cost"] for api in api_usage.values())
            
            # Format API usage for response
            api_usage_list = [
                {
                    "api_name": api_name,
                    "calls": data["calls"],
                    "tokens": data["tokens"],
                    "cost": round(data["cost"], 4)
                }
                for api_name, data in api_usage.items()
            ]
            
            # Sort by cost (highest first)
            api_usage_list.sort(key=lambda x: x["cost"], reverse=True)
            
            return {
                "time_period": time_period,
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "api_usage": api_usage_list
            }
        except Exception as e:
            logger.error(f"Error getting usage summary: {str(e)}")
            return {"error": f"Failed to get usage summary: {str(e)}"}
    
    async def check_rate_limits(self, user_id: str, api_name: str) -> Dict[str, Any]:
        """Check if a user has exceeded rate limits for an API.
        
        Args:
            user_id: ID of the user
            api_name: Name of the API
            
        Returns:
            Dictionary with rate limit information
        """
        try:
            # Get user and organization
            user = await prisma.user.find_unique(
                where={"id": user_id},
                include={"organization": True}
            )
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return {"allowed": False, "error": "User not found"}
            
            # Get rate limits from settings
            rate_limits = self._get_rate_limits(user.role)
            
            # Check daily limit
            daily_limit = rate_limits.get(api_name, {}).get("daily", 1000)
            daily_usage = await self._get_usage_count(user_id, api_name, "day")
            
            # Check monthly limit
            monthly_limit = rate_limits.get(api_name, {}).get("monthly", 10000)
            monthly_usage = await self._get_usage_count(user_id, api_name, "month")
            
            # Determine if allowed
            daily_allowed = daily_usage < daily_limit
            monthly_allowed = monthly_usage < monthly_limit
            allowed = daily_allowed and monthly_allowed
            
            return {
                "allowed": allowed,
                "daily_usage": daily_usage,
                "daily_limit": daily_limit,
                "daily_remaining": max(0, daily_limit - daily_usage),
                "monthly_usage": monthly_usage,
                "monthly_limit": monthly_limit,
                "monthly_remaining": max(0, monthly_limit - monthly_usage),
                "user_role": user.role
            }
        except Exception as e:
            logger.error(f"Error checking rate limits: {str(e)}")
            return {"allowed": False, "error": f"Failed to check rate limits: {str(e)}"}
    
    async def _get_usage_count(self, user_id: str, api_name: str, time_period: str) -> int:
        """Get the number of API calls for a user in a time period.
        
        Args:
            user_id: ID of the user
            api_name: Name of the API
            time_period: Time period (day, week, month)
            
        Returns:
            Number of API calls
        """
        try:
            # Calculate date range
            now = datetime.utcnow()
            if time_period == "day":
                start_date = now - timedelta(days=1)
            elif time_period == "week":
                start_date = now - timedelta(weeks=1)
            elif time_period == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)  # Default to day
            
            # Count API calls
            count = await prisma.aiinteraction.count(
                where={
                    "user_id": user_id,
                    "created_at": {"gte": start_date},
                    "interaction_type": "api_usage",
                    "metadata": {"path": ["api_name"], "equals": api_name}
                }
            )
            
            return count
        except Exception as e:
            logger.error(f"Error getting usage count: {str(e)}")
            return 0
    
    def _calculate_cost(self, api_name: str, tokens: int) -> float:
        """Calculate the cost of an API call based on token usage.
        
        Args:
            api_name: Name of the API
            tokens: Number of tokens used
            
        Returns:
            Estimated cost in USD
        """
        # Define cost per 1000 tokens for different APIs
        # These are approximate costs and should be updated based on actual pricing
        cost_per_1k = {
            "openai.completion.gpt4": 0.03,  # $0.03 per 1K tokens
            "openai.completion.gpt35": 0.002,  # $0.002 per 1K tokens
            "openai.embedding": 0.0001,  # $0.0001 per 1K tokens
            "default": 0.01  # Default cost
        }
        
        # Get cost rate for the API
        rate = cost_per_1k.get(api_name, cost_per_1k["default"])
        
        # Calculate cost
        cost = (tokens / 1000) * rate
        
        return cost
    
    def _get_rate_limits(self, user_role: str) -> Dict[str, Dict[str, int]]:
        """Get rate limits based on user role.
        
        Args:
            user_role: User role (student, professor, admin)
            
        Returns:
            Dictionary with rate limits for different APIs
        """
        # Define rate limits for different roles and APIs
        rate_limits = {
            "STUDENT": {
                "openai.completion": {"daily": 50, "monthly": 1000},
                "openai.embedding": {"daily": 100, "monthly": 2000},
                "default": {"daily": 50, "monthly": 1000}
            },
            "PROFESSOR": {
                "openai.completion": {"daily": 200, "monthly": 5000},
                "openai.embedding": {"daily": 500, "monthly": 10000},
                "default": {"daily": 200, "monthly": 5000}
            },
            "ADMIN": {
                "openai.completion": {"daily": 500, "monthly": 15000},
                "openai.embedding": {"daily": 1000, "monthly": 30000},
                "default": {"daily": 500, "monthly": 15000}
            }
        }
        
        return rate_limits.get(user_role, rate_limits["STUDENT"])

# Create a singleton instance of the APIUsageService
api_usage_service = APIUsageService()
