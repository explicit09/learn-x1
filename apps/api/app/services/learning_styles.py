from typing import List, Dict, Any, Optional
import logging
from prisma.models import User, LearningStyle
from app.services.prisma import prisma

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningStyleService:
    """Service for managing user learning styles and personalization."""
    
    async def get_user_learning_style(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's learning style preferences.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with learning style preferences or None if not found
        """
        try:
            # Get user's learning style
            learning_style = await prisma.learningstyle.find_unique(
                where={"user_id": user_id}
            )
            
            if not learning_style:
                return None
            
            return {
                "id": learning_style.id,
                "user_id": learning_style.user_id,
                "visual_score": learning_style.visual_score,
                "auditory_score": learning_style.auditory_score,
                "reading_score": learning_style.reading_score,
                "kinesthetic_score": learning_style.kinesthetic_score,
                "created_at": learning_style.created_at,
                "updated_at": learning_style.updated_at
            }
        except Exception as e:
            logger.error(f"Error getting user learning style: {str(e)}")
            return None
    
    async def update_user_learning_style(self, user_id: str, style_data: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Update a user's learning style preferences.
        
        Args:
            user_id: ID of the user
            style_data: Dictionary with learning style scores
            
        Returns:
            Updated learning style data or None if failed
        """
        try:
            # Check if user exists
            user = await prisma.user.find_unique(
                where={"id": user_id}
            )
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return None
            
            # Validate scores (must be between 1-10)
            for key, value in style_data.items():
                if key in ["visual_score", "auditory_score", "reading_score", "kinesthetic_score"]:
                    if not isinstance(value, int) or value < 1 or value > 10:
                        logger.error(f"Invalid score for {key}: {value}. Must be an integer between 1-10.")
                        return None
            
            # Check if learning style exists
            existing_style = await prisma.learningstyle.find_unique(
                where={"user_id": user_id}
            )
            
            if existing_style:
                # Update existing learning style
                updated_style = await prisma.learningstyle.update(
                    where={"id": existing_style.id},
                    data={
                        "visual_score": style_data.get("visual_score", existing_style.visual_score),
                        "auditory_score": style_data.get("auditory_score", existing_style.auditory_score),
                        "reading_score": style_data.get("reading_score", existing_style.reading_score),
                        "kinesthetic_score": style_data.get("kinesthetic_score", existing_style.kinesthetic_score)
                    }
                )
            else:
                # Create new learning style
                updated_style = await prisma.learningstyle.create(
                    data={
                        "user_id": user_id,
                        "visual_score": style_data.get("visual_score", 5),
                        "auditory_score": style_data.get("auditory_score", 5),
                        "reading_score": style_data.get("reading_score", 5),
                        "kinesthetic_score": style_data.get("kinesthetic_score", 5)
                    }
                )
            
            return {
                "id": updated_style.id,
                "user_id": updated_style.user_id,
                "visual_score": updated_style.visual_score,
                "auditory_score": updated_style.auditory_score,
                "reading_score": updated_style.reading_score,
                "kinesthetic_score": updated_style.kinesthetic_score,
                "created_at": updated_style.created_at,
                "updated_at": updated_style.updated_at
            }
        except Exception as e:
            logger.error(f"Error updating user learning style: {str(e)}")
            return None
    
    async def get_learning_style_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get personalized learning recommendations based on learning style.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with personalized recommendations
        """
        try:
            # Get user's learning style
            learning_style = await self.get_user_learning_style(user_id)
            
            if not learning_style:
                # Return default recommendations if no learning style found
                return {
                    "primary_style": "balanced",
                    "content_format_preference": "mixed",
                    "study_recommendations": [
                        "Try different learning formats to discover your preferences",
                        "Alternate between reading, watching videos, and interactive exercises",
                        "Take notes in a format that feels most comfortable to you"
                    ],
                    "explanation_style": "balanced"
                }
            
            # Determine primary learning style
            styles = {
                "visual": learning_style["visual_score"],
                "auditory": learning_style["auditory_score"],
                "reading": learning_style["reading_score"],
                "kinesthetic": learning_style["kinesthetic_score"]
            }
            
            primary_style = max(styles, key=styles.get)
            primary_score = styles[primary_style]
            
            # Check if there's a clear preference or balanced style
            is_balanced = all(abs(score - primary_score) <= 2 for score in styles.values())
            
            if is_balanced:
                primary_style = "balanced"
            
            # Generate recommendations based on learning style
            recommendations = {
                "primary_style": primary_style,
                "style_scores": styles,
                "content_format_preference": self._get_content_format_preference(primary_style),
                "study_recommendations": self._get_study_recommendations(primary_style),
                "explanation_style": self._get_explanation_style(primary_style)
            }
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting learning style recommendations: {str(e)}")
            return {
                "primary_style": "balanced",
                "content_format_preference": "mixed",
                "study_recommendations": [
                    "Try different learning formats to discover your preferences",
                    "Alternate between reading, watching videos, and interactive exercises",
                    "Take notes in a format that feels most comfortable to you"
                ],
                "explanation_style": "balanced"
            }
    
    def _get_content_format_preference(self, primary_style: str) -> str:
        """Get preferred content format based on learning style."""
        if primary_style == "visual":
            return "visual"
        elif primary_style == "auditory":
            return "audio"
        elif primary_style == "reading":
            return "text"
        elif primary_style == "kinesthetic":
            return "interactive"
        else:
            return "mixed"
    
    def _get_study_recommendations(self, primary_style: str) -> List[str]:
        """Get study recommendations based on learning style."""
        if primary_style == "visual":
            return [
                "Use diagrams, charts, and mind maps to organize information",
                "Watch video tutorials and demonstrations",
                "Use color-coding in your notes",
                "Visualize concepts and processes in your mind"
            ]
        elif primary_style == "auditory":
            return [
                "Record lectures and listen to them again",
                "Discuss concepts with others or explain them out loud",
                "Use audio materials and podcasts",
                "Read material aloud when studying"
            ]
        elif primary_style == "reading":
            return [
                "Take detailed notes and rewrite them for better retention",
                "Use textbooks and written materials as primary resources",
                "Create written summaries of concepts",
                "Use flashcards for key terms and definitions"
            ]
        elif primary_style == "kinesthetic":
            return [
                "Use hands-on exercises and practical applications",
                "Take breaks and move around while studying",
                "Use physical objects or models when possible",
                "Apply concepts to real-world scenarios"
            ]
        else:
            return [
                "Combine different learning methods for better retention",
                "Alternate between reading, watching videos, and interactive exercises",
                "Try different note-taking methods to find what works best",
                "Use a variety of study materials and approaches"
            ]
    
    def _get_explanation_style(self, primary_style: str) -> str:
        """Get preferred explanation style based on learning style."""
        if primary_style == "visual":
            return "visual"
        elif primary_style == "auditory":
            return "conversational"
        elif primary_style == "reading":
            return "detailed"
        elif primary_style == "kinesthetic":
            return "example-based"
        else:
            return "balanced"

# Create a singleton instance of the LearningStyleService
learning_style_service = LearningStyleService()
