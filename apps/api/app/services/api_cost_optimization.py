from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import json
from app.services.prisma import prisma
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APICostOptimizationService:
    """Service for tracking and optimizing API usage costs."""
    
    # OpenAI model pricing (per 1000 tokens) - May 2025 pricing
    MODEL_COSTS = {
        # Completion models
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        # Embedding models
        "text-embedding-ada-002": {"input": 0.0001, "output": 0.0},
        "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
        "text-embedding-3-large": {"input": 0.00013, "output": 0.0}
    }
    
    # Default model to use for each operation type
    DEFAULT_MODELS = {
        "completion": "gpt-3.5-turbo",
        "embedding": "text-embedding-3-small"
    }
    
    # Model tiers for cost optimization
    MODEL_TIERS = {
        "low": {
            "completion": "gpt-3.5-turbo",
            "embedding": "text-embedding-3-small"
        },
        "medium": {
            "completion": "gpt-3.5-turbo",
            "embedding": "text-embedding-3-large"
        },
        "high": {
            "completion": "gpt-4-turbo",
            "embedding": "text-embedding-3-large"
        },
        "premium": {
            "completion": "gpt-4",
            "embedding": "text-embedding-3-large"
        }
    }
    
    async def calculate_cost(self, model: str, input_tokens: int, output_tokens: int = 0) -> float:
        """Calculate the cost of an API call based on the model and token usage.
        
        Args:
            model: The model used for the API call
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (0 for embedding models)
            
        Returns:
            The cost in USD
        """
        if model not in self.MODEL_COSTS:
            logger.warning(f"Unknown model: {model}, using gpt-3.5-turbo pricing")
            model = "gpt-3.5-turbo"
        
        model_cost = self.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * model_cost["input"]
        output_cost = (output_tokens / 1000) * model_cost["output"]
        
        return input_cost + output_cost
    
    async def log_api_cost(self, organization_id: str, user_id: str, model: str, 
                          input_tokens: int, output_tokens: int, 
                          interaction_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Log the cost of an API call to the database.
        
        Args:
            organization_id: ID of the organization
            user_id: ID of the user
            model: The model used for the API call
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            interaction_type: Type of interaction (e.g., 'ask', 'quiz', 'embedding')
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with cost information
        """
        try:
            cost = await self.calculate_cost(model, input_tokens, output_tokens)
            
            # Create metadata if not provided
            if metadata is None:
                metadata = {}
            
            # Add cost information to metadata
            metadata["cost"] = cost
            metadata["model"] = model
            metadata["input_tokens"] = input_tokens
            metadata["output_tokens"] = output_tokens
            
            # Log the interaction in the database
            interaction = await prisma.aiinteraction.create(
                data={
                    "organization_id": organization_id,
                    "user_id": user_id,
                    "interaction_type": interaction_type,
                    "tokens_used": input_tokens + output_tokens,
                    "cost": cost,
                    "model": model,
                    "metadata": metadata
                }
            )
            
            return {
                "interaction_id": interaction.id,
                "cost": cost,
                "tokens_used": input_tokens + output_tokens,
                "model": model,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error logging API cost: {str(e)}")
            return {
                "error": f"Failed to log API cost: {str(e)}",
                "cost": await self.calculate_cost(model, input_tokens, output_tokens),
                "tokens_used": input_tokens + output_tokens,
                "model": model,
                "status": "error"
            }
    
    async def get_cost_summary(self, organization_id: str, time_period: str = "month") -> Dict[str, Any]:
        """Get a summary of API costs for an organization.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for the summary (day, week, month, year)
            
        Returns:
            Dictionary with cost summary information
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
            
            # Get all interactions for the organization in the time period
            interactions = await prisma.aiinteraction.find_many(
                where={
                    "organization_id": organization_id,
                    "created_at": {"gte": start_date}
                }
            )
            
            if not interactions:
                return {
                    "time_period": time_period,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "interaction_count": 0,
                    "message": "No interactions in the specified time period"
                }
            
            # Calculate total cost and tokens
            total_cost = sum(interaction.cost or 0 for interaction in interactions)
            total_tokens = sum(interaction.tokens_used or 0 for interaction in interactions)
            
            # Group by interaction type
            cost_by_type = {}
            for interaction in interactions:
                interaction_type = interaction.interaction_type or "unknown"
                
                if interaction_type not in cost_by_type:
                    cost_by_type[interaction_type] = {
                        "count": 0,
                        "cost": 0.0,
                        "tokens": 0
                    }
                
                cost_by_type[interaction_type]["count"] += 1
                cost_by_type[interaction_type]["cost"] += interaction.cost or 0
                cost_by_type[interaction_type]["tokens"] += interaction.tokens_used or 0
            
            # Group by model
            cost_by_model = {}
            for interaction in interactions:
                model = interaction.model or "unknown"
                
                if model not in cost_by_model:
                    cost_by_model[model] = {
                        "count": 0,
                        "cost": 0.0,
                        "tokens": 0
                    }
                
                cost_by_model[model]["count"] += 1
                cost_by_model[model]["cost"] += interaction.cost or 0
                cost_by_model[model]["tokens"] += interaction.tokens_used or 0
            
            # Format cost by type for response
            cost_by_type_list = [
                {
                    "interaction_type": interaction_type,
                    "count": data["count"],
                    "cost": round(data["cost"], 4),
                    "tokens": data["tokens"],
                    "percentage": round((data["cost"] / total_cost) * 100, 2) if total_cost > 0 else 0
                }
                for interaction_type, data in cost_by_type.items()
            ]
            
            # Format cost by model for response
            cost_by_model_list = [
                {
                    "model": model,
                    "count": data["count"],
                    "cost": round(data["cost"], 4),
                    "tokens": data["tokens"],
                    "percentage": round((data["cost"] / total_cost) * 100, 2) if total_cost > 0 else 0
                }
                for model, data in cost_by_model.items()
            ]
            
            # Sort by cost (highest first)
            cost_by_type_list.sort(key=lambda x: x["cost"], reverse=True)
            cost_by_model_list.sort(key=lambda x: x["cost"], reverse=True)
            
            return {
                "time_period": time_period,
                "total_cost": round(total_cost, 4),
                "total_tokens": total_tokens,
                "interaction_count": len(interactions),
                "cost_by_type": cost_by_type_list,
                "cost_by_model": cost_by_model_list,
                "average_cost_per_interaction": round(total_cost / len(interactions), 4) if interactions else 0
            }
        except Exception as e:
            logger.error(f"Error getting cost summary: {str(e)}")
            return {"error": f"Failed to get cost summary: {str(e)}"}
    
    async def get_cost_by_user(self, organization_id: str, time_period: str = "month") -> Dict[str, Any]:
        """Get a breakdown of API costs by user for an organization.
        
        Args:
            organization_id: ID of the organization
            time_period: Time period for the summary (day, week, month, year)
            
        Returns:
            Dictionary with cost breakdown by user
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
            
            user_map = {user.id: user for user in users}
            
            # Get all interactions for the organization in the time period
            interactions = await prisma.aiinteraction.find_many(
                where={
                    "organization_id": organization_id,
                    "created_at": {"gte": start_date}
                }
            )
            
            if not interactions:
                return {
                    "time_period": time_period,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "interaction_count": 0,
                    "message": "No interactions in the specified time period"
                }
            
            # Calculate total cost and tokens
            total_cost = sum(interaction.cost or 0 for interaction in interactions)
            total_tokens = sum(interaction.tokens_used or 0 for interaction in interactions)
            
            # Group by user
            cost_by_user = {}
            for interaction in interactions:
                user_id = interaction.user_id
                
                if user_id not in cost_by_user:
                    user = user_map.get(user_id)
                    user_email = user.email if user else "unknown"
                    user_name = user.name if user and user.name else user_email
                    
                    cost_by_user[user_id] = {
                        "user_id": user_id,
                        "user_email": user_email,
                        "user_name": user_name,
                        "count": 0,
                        "cost": 0.0,
                        "tokens": 0
                    }
                
                cost_by_user[user_id]["count"] += 1
                cost_by_user[user_id]["cost"] += interaction.cost or 0
                cost_by_user[user_id]["tokens"] += interaction.tokens_used or 0
            
            # Format cost by user for response
            cost_by_user_list = [
                {
                    "user_id": data["user_id"],
                    "user_email": data["user_email"],
                    "user_name": data["user_name"],
                    "count": data["count"],
                    "cost": round(data["cost"], 4),
                    "tokens": data["tokens"],
                    "percentage": round((data["cost"] / total_cost) * 100, 2) if total_cost > 0 else 0
                }
                for user_id, data in cost_by_user.items()
            ]
            
            # Sort by cost (highest first)
            cost_by_user_list.sort(key=lambda x: x["cost"], reverse=True)
            
            return {
                "time_period": time_period,
                "total_cost": round(total_cost, 4),
                "total_tokens": total_tokens,
                "interaction_count": len(interactions),
                "cost_by_user": cost_by_user_list,
                "average_cost_per_user": round(total_cost / len(cost_by_user), 4) if cost_by_user else 0
            }
        except Exception as e:
            logger.error(f"Error getting cost by user: {str(e)}")
            return {"error": f"Failed to get cost by user: {str(e)}"}
    
    async def recommend_cost_optimizations(self, organization_id: str) -> Dict[str, Any]:
        """Recommend cost optimizations based on usage patterns.
        
        Args:
            organization_id: ID of the organization
            
        Returns:
            Dictionary with optimization recommendations
        """
        try:
            # Get cost summary for the last month
            cost_summary = await self.get_cost_summary(organization_id, "month")
            
            if "error" in cost_summary:
                return {"error": cost_summary["error"]}
            
            recommendations = []
            estimated_savings = 0.0
            
            # Check if there's significant usage of expensive models
            for model_data in cost_summary.get("cost_by_model", []):
                model = model_data["model"]
                cost = model_data["cost"]
                tokens = model_data["tokens"]
                count = model_data["count"]
                
                # Recommend cheaper models for non-critical operations
                if model == "gpt-4" and count > 10:
                    # Calculate potential savings by switching to gpt-4-turbo
                    potential_savings = cost * 0.5  # Approximately 50% cheaper
                    recommendations.append({
                        "recommendation": "Switch from gpt-4 to gpt-4-turbo for most operations",
                        "current_model": "gpt-4",
                        "recommended_model": "gpt-4-turbo",
                        "current_cost": round(cost, 4),
                        "estimated_new_cost": round(cost * 0.5, 4),
                        "estimated_savings": round(potential_savings, 4),
                        "impact": "medium",
                        "implementation_difficulty": "low"
                    })
                    estimated_savings += potential_savings
                
                # Recommend using smaller embedding models where appropriate
                if model == "text-embedding-3-large" and count > 100:
                    # Calculate potential savings by switching to text-embedding-3-small
                    potential_savings = cost * 0.85  # Approximately 85% cheaper
                    recommendations.append({
                        "recommendation": "Use text-embedding-3-small for most embedding operations",
                        "current_model": "text-embedding-3-large",
                        "recommended_model": "text-embedding-3-small",
                        "current_cost": round(cost, 4),
                        "estimated_new_cost": round(cost * 0.15, 4),
                        "estimated_savings": round(potential_savings, 4),
                        "impact": "low",
                        "implementation_difficulty": "low"
                    })
                    estimated_savings += potential_savings
            
            # Check for high token usage in specific interaction types
            for type_data in cost_summary.get("cost_by_type", []):
                interaction_type = type_data["interaction_type"]
                cost = type_data["cost"]
                tokens = type_data["tokens"]
                count = type_data["count"]
                
                # Recommend caching for frequently repeated operations
                if interaction_type == "embedding" and count > 1000:
                    potential_savings = cost * 0.4  # Estimate 40% savings with caching
                    recommendations.append({
                        "recommendation": "Implement caching for embedding operations",
                        "interaction_type": interaction_type,
                        "current_cost": round(cost, 4),
                        "estimated_new_cost": round(cost * 0.6, 4),
                        "estimated_savings": round(potential_savings, 4),
                        "impact": "medium",
                        "implementation_difficulty": "medium"
                    })
                    estimated_savings += potential_savings
                
                # Recommend batch processing for quiz generation
                if interaction_type == "quiz" and count > 50:
                    potential_savings = cost * 0.25  # Estimate 25% savings with batching
                    recommendations.append({
                        "recommendation": "Implement batch processing for quiz generation",
                        "interaction_type": interaction_type,
                        "current_cost": round(cost, 4),
                        "estimated_new_cost": round(cost * 0.75, 4),
                        "estimated_savings": round(potential_savings, 4),
                        "impact": "medium",
                        "implementation_difficulty": "high"
                    })
                    estimated_savings += potential_savings
            
            # Add general recommendations if total cost is significant
            if cost_summary.get("total_cost", 0) > 100:
                recommendations.append({
                    "recommendation": "Implement tiered access to AI features based on user roles",
                    "estimated_savings": "Variable",
                    "impact": "high",
                    "implementation_difficulty": "medium"
                })
                
                recommendations.append({
                    "recommendation": "Set up usage quotas per user or department",
                    "estimated_savings": "Variable",
                    "impact": "high",
                    "implementation_difficulty": "medium"
                })
            
            # Sort recommendations by estimated savings (highest first)
            recommendations.sort(
                key=lambda x: float(x["estimated_savings"]) if isinstance(x["estimated_savings"], (int, float)) else 0, 
                reverse=True
            )
            
            return {
                "total_current_cost": round(cost_summary.get("total_cost", 0), 4),
                "estimated_savings": round(estimated_savings, 4),
                "estimated_optimized_cost": round(cost_summary.get("total_cost", 0) - estimated_savings, 4),
                "savings_percentage": round((estimated_savings / cost_summary.get("total_cost", 1)) * 100, 2) if cost_summary.get("total_cost", 0) > 0 else 0,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"Error generating cost optimization recommendations: {str(e)}")
            return {"error": f"Failed to generate cost optimization recommendations: {str(e)}"}
    
    async def get_recommended_model(self, interaction_type: str, user_role: str, 
                                  content_complexity: Optional[str] = None) -> str:
        """Get the recommended model for a specific interaction type based on user role and content complexity.
        
        Args:
            interaction_type: Type of interaction (e.g., 'completion', 'embedding')
            user_role: Role of the user (e.g., 'student', 'professor', 'admin')
            content_complexity: Complexity of the content (e.g., 'low', 'medium', 'high')
            
        Returns:
            The recommended model name
        """
        # Default to medium complexity if not specified
        if content_complexity is None:
            content_complexity = "medium"
        
        # Map user roles to model tiers
        role_tiers = {
            "student": "low",
            "professor": "medium",
            "admin": "high",
            "super_admin": "premium"
        }
        
        # Get the tier based on user role
        tier = role_tiers.get(user_role, "low")
        
        # Adjust tier based on content complexity
        if content_complexity == "high" and tier != "premium":
            # Increase tier by one level for high complexity content
            if tier == "low":
                tier = "medium"
            elif tier == "medium":
                tier = "high"
        
        # Get the recommended model for the tier and interaction type
        if interaction_type not in ["completion", "embedding"]:
            interaction_type = "completion"  # Default to completion for unknown types
        
        return self.MODEL_TIERS[tier][interaction_type]

# Create a singleton instance of the APICostOptimizationService
api_cost_optimization_service = APICostOptimizationService()
