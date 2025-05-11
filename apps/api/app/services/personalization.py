from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from datetime import datetime, timedelta

from app.services.prisma import prisma
from app.services.openai import openai_service
from app.services.learning_styles import learning_style_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonalizationService:
    """
    Service for implementing personalization features in the LEARN-X platform.
    
    This service provides personalization capabilities including:
    - User preference management
    - Learning style assessment and recommendations
    - Personalized content recommendations
    - Adaptive learning paths
    - Personalized UI settings
    - Study plan generation
    """
    
    def __init__(self):
        """Initialize the personalization service."""
        self.preference_defaults = {
            "content_format": "mixed",  # Options: text, video, interactive, mixed
            "difficulty_level": "adaptive",  # Options: beginner, intermediate, advanced, adaptive
            "ui_theme": "system",  # Options: light, dark, system
            "notification_frequency": "daily",  # Options: none, daily, weekly
            "language": "en",  # Default language
        }
    
    async def connect(self) -> None:
        """Connect to required services."""
        pass  # No specific connection needed
    
    async def disconnect(self) -> None:
        """Disconnect from services."""
        pass  # No specific disconnection needed
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences for personalization.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary of user preferences
        """
        try:
            # Get user preferences from database
            user_preference = await prisma.userpreference.find_unique(
                where={"userId": user_id}
            )
            
            # Start with default preferences
            preferences = self.preference_defaults.copy()
            
            if user_preference:
                # Update with stored preferences
                if user_preference.ui_preferences:
                    try:
                        ui_prefs = json.loads(user_preference.ui_preferences)
                        preferences.update(ui_prefs)
                    except json.JSONDecodeError:
                        logger.error(f"Error parsing UI preferences for user {user_id}")
                
                # Add learning style if available
                if user_preference.learning_style:
                    preferences["learning_style"] = user_preference.learning_style
                
                # Add interests if available
                if user_preference.interests:
                    try:
                        interests = json.loads(user_preference.interests)
                        preferences["interests"] = interests
                    except json.JSONDecodeError:
                        logger.error(f"Error parsing interests for user {user_id}")
            
            # Get learning style data
            learning_style = await learning_style_service.get_user_learning_style(user_id)
            if learning_style:
                preferences["learning_style_details"] = {
                    "visual_score": learning_style.get("visual_score", 0),
                    "auditory_score": learning_style.get("auditory_score", 0),
                    "reading_score": learning_style.get("reading_score", 0),
                    "kinesthetic_score": learning_style.get("kinesthetic_score", 0)
                }
                
                # Determine primary learning style
                scores = [
                    ("visual", preferences["learning_style_details"]["visual_score"]),
                    ("auditory", preferences["learning_style_details"]["auditory_score"]),
                    ("reading", preferences["learning_style_details"]["reading_score"]),
                    ("kinesthetic", preferences["learning_style_details"]["kinesthetic_score"])
                ]
                primary_style = max(scores, key=lambda x: x[1])[0]
                preferences["primary_learning_style"] = primary_style
            
            return preferences
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return self.preference_defaults.copy()
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences.
        
        Args:
            user_id: The user's ID
            preferences: Dictionary of preferences to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing user preference
            user_preference = await prisma.userpreference.find_unique(
                where={"userId": user_id}
            )
            
            # Prepare data for update
            ui_preferences = {}
            interests = []
            learning_style = None
            
            # Extract UI preferences
            for key, value in preferences.items():
                if key == "interests":
                    interests = value
                elif key == "learning_style":
                    learning_style = value
                else:
                    ui_preferences[key] = value
            
            # Convert to JSON strings
            ui_preferences_json = json.dumps(ui_preferences) if ui_preferences else None
            interests_json = json.dumps(interests) if interests else None
            
            if user_preference:
                # Update existing preference
                await prisma.userpreference.update(
                    where={"id": user_preference.id},
                    data={
                        "ui_preferences": ui_preferences_json,
                        "interests": interests_json,
                        "learning_style": learning_style
                    }
                )
            else:
                # Create new preference
                await prisma.userpreference.create(
                    data={
                        "userId": user_id,
                        "ui_preferences": ui_preferences_json,
                        "interests": interests_json,
                        "learning_style": learning_style
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            return False
    
    async def get_personalized_recommendations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get personalized content recommendations for a user.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended materials
        """
        try:
            # Get user preferences and learning history
            preferences = await self.get_user_preferences(user_id)
            learning_history = await self._get_user_learning_history(user_id)
            
            # Get user's organization
            user = await prisma.user.find_unique(
                where={"id": user_id},
                include={"organization": True}
            )
            
            if not user or not user.organization:
                return []
            
            organization_id = user.organization.id
            
            # Get materials from user's organization
            materials = await prisma.material.find_many(
                where={
                    "organizationId": organization_id,
                    "status": "PUBLISHED"
                },
                include={
                    "topic": True
                },
                take=50  # Get a larger pool to filter from
            )
            
            if not materials:
                return []
            
            # Filter out materials the user has already completed
            completed_material_ids = set()
            for material_id, history in learning_history.items():
                if history.get("completed", False):
                    completed_material_ids.add(material_id)
            
            available_materials = [m for m in materials if m.id not in completed_material_ids]
            
            if not available_materials:
                return []
            
            # Score materials based on user preferences and learning history
            scored_materials = []
            for material in available_materials:
                score = await self._calculate_recommendation_score(material, preferences, learning_history)
                scored_materials.append((material, score))
            
            # Sort by score (descending) and take top recommendations
            scored_materials.sort(key=lambda x: x[1], reverse=True)
            top_recommendations = scored_materials[:limit]
            
            # Format recommendations
            recommendations = []
            for material, score in top_recommendations:
                recommendations.append({
                    "id": material.id,
                    "title": material.title,
                    "type": material.type,
                    "topic": material.topic.name if material.topic else None,
                    "recommendation_score": score,
                    "recommendation_reason": await self._get_recommendation_reason(material, preferences, score)
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {str(e)}")
            return []
    
    async def _calculate_recommendation_score(self, 
                                             material: Any, 
                                             preferences: Dict[str, Any], 
                                             learning_history: Dict[str, Dict[str, Any]]) -> float:
        """Calculate recommendation score for a material based on user preferences.
        
        Args:
            material: Material to score
            preferences: User preferences
            learning_history: User's learning history
            
        Returns:
            Recommendation score (0-1)
        """
        score = 0.5  # Base score
        
        # Adjust based on material type and preferred content format
        content_format = preferences.get("content_format", "mixed")
        if content_format != "mixed":
            if content_format == "text" and material.type in ["DOCUMENT", "ARTICLE"]:
                score += 0.2
            elif content_format == "video" and material.type == "VIDEO":
                score += 0.2
            elif content_format == "interactive" and material.type in ["INTERACTIVE", "QUIZ"]:
                score += 0.2
        
        # Adjust based on user interests
        if "interests" in preferences and material.topic:
            interests = preferences["interests"]
            if material.topic.name.lower() in [interest.lower() for interest in interests]:
                score += 0.3
        
        # Adjust based on learning path progression
        if material.topic and material.topic.id in learning_history.get("topic_progress", {}):
            topic_progress = learning_history["topic_progress"][material.topic.id]
            if topic_progress.get("completed_count", 0) > 0:
                # User has made progress in this topic, boost score
                score += 0.1
        
        # Cap score at 1.0
        return min(score, 1.0)
    
    async def _get_recommendation_reason(self, 
                                        material: Any, 
                                        preferences: Dict[str, Any], 
                                        score: float) -> str:
        """Generate a human-readable reason for the recommendation.
        
        Args:
            material: Recommended material
            preferences: User preferences
            score: Recommendation score
            
        Returns:
            Recommendation reason
        """
        reasons = []
        
        # Reason based on content format
        content_format = preferences.get("content_format", "mixed")
        if content_format != "mixed":
            if content_format == "text" and material.type in ["DOCUMENT", "ARTICLE"]:
                reasons.append("Matches your preference for text-based content")
            elif content_format == "video" and material.type == "VIDEO":
                reasons.append("Matches your preference for video content")
            elif content_format == "interactive" and material.type in ["INTERACTIVE", "QUIZ"]:
                reasons.append("Matches your preference for interactive content")
        
        # Reason based on learning style
        if "primary_learning_style" in preferences:
            primary_style = preferences["primary_learning_style"]
            if primary_style == "visual" and material.type in ["VIDEO", "INTERACTIVE"]:
                reasons.append("Suitable for your visual learning style")
            elif primary_style == "auditory" and material.type == "VIDEO":
                reasons.append("Suitable for your auditory learning style")
            elif primary_style == "reading" and material.type in ["DOCUMENT", "ARTICLE"]:
                reasons.append("Suitable for your reading/writing learning style")
            elif primary_style == "kinesthetic" and material.type == "INTERACTIVE":
                reasons.append("Suitable for your kinesthetic learning style")
        
        # Reason based on interests
        if "interests" in preferences and material.topic:
            interests = preferences["interests"]
            if material.topic.name.lower() in [interest.lower() for interest in interests]:
                reasons.append(f"Related to your interest in {material.topic.name}")
        
        # Fallback reason
        if not reasons:
            if score > 0.8:
                reasons.append("Highly recommended based on your learning profile")
            elif score > 0.6:
                reasons.append("Recommended based on your learning profile")
            else:
                reasons.append("May be relevant to your learning journey")
        
        return "; ".join(reasons)
    
    async def _get_user_learning_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's learning history.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with learning history data
        """
        try:
            # Get user's interactions with materials
            interactions = await prisma.userinteraction.find_many(
                where={
                    "userId": user_id,
                    "type": {"in": ["VIEW", "COMPLETE", "QUIZ"]}
                },
                order_by={
                    "createdAt": "desc"
                },
                include={
                    "material": {
                        "include": {
                            "topic": True
                        }
                    }
                },
                take=100  # Limit to recent interactions
            )
            
            # Organize by material ID
            material_history = {}
            topic_progress = {}
            
            for interaction in interactions:
                if not interaction.material:
                    continue
                
                material_id = interaction.material.id
                if material_id not in material_history:
                    material_history[material_id] = {
                        "interaction_count": 0,
                        "last_interaction": None,
                        "completed": False
                    }
                
                material_history[material_id]["interaction_count"] += 1
                
                # Update last interaction time
                if not material_history[material_id]["last_interaction"] or \
                   interaction.created_at > material_history[material_id]["last_interaction"]:
                    material_history[material_id]["last_interaction"] = interaction.created_at
                
                # Check if material was completed
                if interaction.type == "COMPLETE":
                    material_history[material_id]["completed"] = True
                
                # Update topic progress
                if interaction.material.topic:
                    topic_id = interaction.material.topic.id
                    if topic_id not in topic_progress:
                        topic_progress[topic_id] = {
                            "name": interaction.material.topic.name,
                            "interaction_count": 0,
                            "completed_count": 0,
                            "last_interaction": None
                        }
                    
                    topic_progress[topic_id]["interaction_count"] += 1
                    
                    if interaction.type == "COMPLETE":
                        topic_progress[topic_id]["completed_count"] += 1
                    
                    if not topic_progress[topic_id]["last_interaction"] or \
                       interaction.created_at > topic_progress[topic_id]["last_interaction"]:
                        topic_progress[topic_id]["last_interaction"] = interaction.created_at
            
            return {
                "materials": material_history,
                "topic_progress": topic_progress
            }
        except Exception as e:
            logger.error(f"Error getting user learning history: {str(e)}")
            return {"materials": {}, "topic_progress": {}}
    
    async def generate_personalized_study_plan(self, user_id: str, topic_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a personalized study plan for a user.
        
        Args:
            user_id: The user's ID
            topic_id: Optional topic ID to focus on
            
        Returns:
            Dictionary with study plan details
        """
        try:
            # Get user preferences and learning history
            preferences = await self.get_user_preferences(user_id)
            learning_history = await self._get_user_learning_history(user_id)
            
            # Get user's organization
            user = await prisma.user.find_unique(
                where={"id": user_id},
                include={"organization": True}
            )
            
            if not user or not user.organization:
                return {"error": "User or organization not found"}
            
            organization_id = user.organization.id
            
            # Get materials for the study plan
            materials_query = {
                "organizationId": organization_id,
                "status": "PUBLISHED"
            }
            
            if topic_id:
                materials_query["topicId"] = topic_id
            
            materials = await prisma.material.find_many(
                where=materials_query,
                include={
                    "topic": True
                },
                order_by={
                    "createdAt": "asc"  # Start with older materials first
                }
            )
            
            if not materials:
                return {"error": "No materials found for study plan"}
            
            # Get completed materials
            completed_material_ids = set()
            for material_id, history in learning_history.get("materials", {}).items():
                if history.get("completed", False):
                    completed_material_ids.add(material_id)
            
            # Filter and organize materials by topic
            topics_map = {}
            for material in materials:
                if not material.topic:
                    continue
                
                topic_id = material.topic.id
                if topic_id not in topics_map:
                    topics_map[topic_id] = {
                        "id": topic_id,
                        "name": material.topic.name,
                        "materials": [],
                        "completed_count": 0,
                        "total_count": 0
                    }
                
                # Add material to topic
                material_data = {
                    "id": material.id,
                    "title": material.title,
                    "type": material.type,
                    "completed": material.id in completed_material_ids
                }
                
                topics_map[topic_id]["materials"].append(material_data)
                topics_map[topic_id]["total_count"] += 1
                
                if material.id in completed_material_ids:
                    topics_map[topic_id]["completed_count"] += 1
            
            # Convert to list and calculate progress
            topics = []
            for topic_data in topics_map.values():
                if topic_data["total_count"] > 0:
                    topic_data["progress"] = (topic_data["completed_count"] / topic_data["total_count"]) * 100
                else:
                    topic_data["progress"] = 0
                
                topics.append(topic_data)
            
            # Sort topics by progress (ascending, so least complete first)
            topics.sort(key=lambda x: x["progress"])
            
            # Generate study plan
            study_plan = {
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "topics": topics,
                "recommendations": []
            }
            
            # Add personalized recommendations
            for topic in topics:
                # Skip topics that are 100% complete
                if topic["progress"] == 100:
                    continue
                
                # Find incomplete materials
                incomplete_materials = [m for m in topic["materials"] if not m["completed"]]
                
                if incomplete_materials:
                    # Sort by learning style preference if available
                    if "primary_learning_style" in preferences:
                        primary_style = preferences["primary_learning_style"]
                        
                        # Assign scores based on learning style and material type
                        scored_materials = []
                        for material in incomplete_materials:
                            score = 0.5  # Base score
                            
                            # Adjust score based on learning style
                            if primary_style == "visual" and material["type"] in ["VIDEO", "INTERACTIVE"]:
                                score += 0.3
                            elif primary_style == "auditory" and material["type"] == "VIDEO":
                                score += 0.3
                            elif primary_style == "reading" and material["type"] in ["DOCUMENT", "ARTICLE"]:
                                score += 0.3
                            elif primary_style == "kinesthetic" and material["type"] == "INTERACTIVE":
                                score += 0.3
                            
                            scored_materials.append((material, score))
                        
                        # Sort by score (descending)
                        scored_materials.sort(key=lambda x: x[1], reverse=True)
                        
                        # Take top 2 materials from each topic
                        for material, score in scored_materials[:2]:
                            study_plan["recommendations"].append({
                                "material_id": material["id"],
                                "title": material["title"],
                                "type": material["type"],
                                "topic_name": topic["name"],
                                "topic_id": topic["id"],
                                "reason": f"Continue your progress in {topic['name']}"
                            })
                    else:
                        # Without learning style, just take the first 2 incomplete materials
                        for material in incomplete_materials[:2]:
                            study_plan["recommendations"].append({
                                "material_id": material["id"],
                                "title": material["title"],
                                "type": material["type"],
                                "topic_name": topic["name"],
                                "topic_id": topic["id"],
                                "reason": f"Continue your progress in {topic['name']}"
                            })
            
            # Limit to top 5 recommendations
            study_plan["recommendations"] = study_plan["recommendations"][:5]
            
            return study_plan
        except Exception as e:
            logger.error(f"Error generating personalized study plan: {str(e)}")
            return {"error": f"Failed to generate study plan: {str(e)}"}
    
    async def get_adaptive_difficulty(self, user_id: str, topic_id: Optional[str] = None) -> str:
        """Get adaptive difficulty level for a user based on their performance.
        
        Args:
            user_id: The user's ID
            topic_id: Optional topic ID to focus on
            
        Returns:
            Difficulty level (beginner, intermediate, advanced)
        """
        try:
            # Get user's quiz performance
            quiz_results = await prisma.quizresult.find_many(
                where={
                    "userId": user_id,
                    "quiz": {
                        "material": {
                            "topicId": topic_id
                        } if topic_id else None
                    }
                },
                include={
                    "quiz": True
                },
                order_by={
                    "createdAt": "desc"
                },
                take=10  # Consider recent quiz results
            )
            
            if not quiz_results:
                return "beginner"  # Default to beginner if no quiz results
            
            # Calculate average score
            total_score = 0
            total_possible = 0
            
            for result in quiz_results:
                total_score += result.score
                total_possible += result.possible_score
            
            if total_possible == 0:
                return "beginner"  # Default to beginner if no possible score
            
            average_percentage = (total_score / total_possible) * 100
            
            # Determine difficulty level based on average score
            if average_percentage < 60:
                return "beginner"
            elif average_percentage < 85:
                return "intermediate"
            else:
                return "advanced"
        except Exception as e:
            logger.error(f"Error getting adaptive difficulty: {str(e)}")
            return "beginner"  # Default to beginner on error
    
    async def get_personalized_ui_settings(self, user_id: str) -> Dict[str, Any]:
        """Get personalized UI settings for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with UI settings
        """
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(user_id)
            
            # Extract UI-related settings
            ui_settings = {
                "theme": preferences.get("ui_theme", "system"),
                "font_size": preferences.get("font_size", "medium"),
                "content_density": preferences.get("content_density", "standard"),
                "animations": preferences.get("animations", True),
                "sidebar_collapsed": preferences.get("sidebar_collapsed", False),
                "notifications_enabled": preferences.get("notifications_enabled", True),
                "notification_frequency": preferences.get("notification_frequency", "daily"),
                "language": preferences.get("language", "en")
            }
            
            return ui_settings
        except Exception as e:
            logger.error(f"Error getting personalized UI settings: {str(e)}")
            return {
                "theme": "system",
                "font_size": "medium",
                "content_density": "standard",
                "animations": True,
                "sidebar_collapsed": False,
                "notifications_enabled": True,
                "notification_frequency": "daily",
                "language": "en"
            }

# Create a singleton instance
personalization_service = PersonalizationService()
