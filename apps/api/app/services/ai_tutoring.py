from typing import List, Dict, Any, Optional
import logging
from prisma.models import AIInteraction, User, Material, Course
from app.services.openai import openai_service
from app.services.embeddings import embeddings_service
from app.services.prisma import prisma
from app.services.learning_styles import learning_style_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AITutoringService:
    """Service for AI tutoring and student assistance."""
    
    async def answer_question(self, user_id: str, query: str, course_id: Optional[str] = None, material_id: Optional[str] = None) -> Dict[str, Any]:
        """Answer a student's question with context-aware responses.
        
        Args:
            user_id: ID of the user asking the question
            query: The question or query from the user
            course_id: Optional course ID for context
            material_id: Optional material ID for context
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get user information
            user = await prisma.user.find_unique(where={"id": user_id})
            if not user:
                logger.error(f"User not found: {user_id}")
                return {"error": "User not found"}
            
            # Retrieve relevant context
            context = await self._get_context(query, course_id, material_id)
            context_text = "\n\n".join([item["content"] for item in context])
            
            # Get user's learning style recommendations
            learning_style_recs = await learning_style_service.get_learning_style_recommendations(user_id)
            explanation_style = learning_style_recs.get("explanation_style", "balanced")
            primary_style = learning_style_recs.get("primary_style", "balanced")
            
            # Tailor response based on learning style
            style_guidance = ""
            if explanation_style == "visual":
                style_guidance = "Use visual descriptions, diagrams, and spatial relationships. Describe how things look and their visual characteristics. Suggest visualizations when explaining concepts."
            elif explanation_style == "conversational":
                style_guidance = "Use a conversational tone with rhythm and flow. Explain concepts as if you're having a discussion. Use analogies and metaphors that relate to sounds or conversations."
            elif explanation_style == "detailed":
                style_guidance = "Provide detailed, text-based explanations with clear structure. Use lists, definitions, and precise language. Be thorough and systematic in your explanations."
            elif explanation_style == "example-based":
                style_guidance = "Focus on practical examples and applications. Relate concepts to real-world scenarios. Suggest activities or exercises that apply the concepts being discussed."
            else:  # balanced
                style_guidance = "Use a balanced approach combining visual descriptions, conversational elements, detailed explanations, and practical examples."
            
            # Prepare system message with context and learning style
            system_message = f"""
            You are an AI tutor for the LEARN-X platform. Your goal is to help students understand concepts and answer their questions.
            
            User Information:
            - Name: {user.name}
            - Role: {user.role}
            - Primary Learning Style: {primary_style}
            
            When answering, follow these guidelines:
            1. Be clear, concise, and educational in your responses
            2. If you're not sure about an answer, acknowledge the limitations
            3. Provide examples when possible to illustrate concepts
            4. Use a friendly, supportive tone
            5. Format your responses using markdown for readability
            
            Learning Style Guidance:
            {style_guidance}
            
            Relevant Context:
            {context_text}
            """
            
            # Generate response using OpenAI
            response = await openai_service.generate_completion(
                prompt=query,
                system_message=system_message,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Detect confusion level (1-10 scale)
            confusion_level = await self._detect_confusion_level(query)
            
            # Generate adaptive follow-up if needed
            follow_up = None
            if confusion_level >= 6:
                follow_up = await self.get_adaptive_follow_up(user_id, query, response, confusion_level)
            
            # Store interaction in database
            interaction = await prisma.aiinteraction.create(
                data={
                    "user_id": user_id,
                    "query": query,
                    "response": response,
                    "context": context_text[:1000] if context_text else None,  # Limit context size
                    "confusion_level": confusion_level,
                    "metadata": {"follow_up": follow_up} if follow_up else None
                }
            )
            
            return {
                "response": response,
                "interaction_id": interaction.id,
                "confusion_level": confusion_level,
                "follow_up": follow_up,
                "learning_style": primary_style,
                "context_sources": [{
                    "title": item.get("title", "Unknown"),
                    "material_id": item.get("material_id"),
                    "similarity": item.get("similarity", 0)
                } for item in context]
            }
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {"error": f"Failed to generate response: {str(e)}"}
    
    async def _get_context(self, query: str, course_id: Optional[str] = None, material_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context for the query.
        
        Args:
            query: The user's question
            course_id: Optional course ID to limit context
            material_id: Optional material ID to limit context
            
        Returns:
            List of context items with content and metadata
        """
        # Search for similar content using embeddings
        similar_content = await embeddings_service.search_similar_content(query, limit=3)
        
        # If material_id is provided, get that specific material
        if material_id:
            material = await prisma.material.find_unique(
                where={"id": material_id},
                include={"course": True}
            )
            if material:
                return [{
                    "content": material.content,
                    "title": material.title,
                    "material_id": material.id,
                    "course_id": material.course.id if material.course else None,
                    "similarity": 1.0  # Explicitly requested material
                }]
        
        # If course_id is provided, get relevant materials from that course
        if course_id and not similar_content:
            materials = await prisma.material.find_many(
                where={"course_id": course_id},
                take=3
            )
            return [{
                "content": material.content,
                "title": material.title,
                "material_id": material.id,
                "course_id": course_id,
                "similarity": 0.5  # Course-related material
            } for material in materials]
        
        return similar_content
    
    async def _detect_confusion_level(self, query: str) -> int:
        """Detect the confusion level in the user's query on a scale of 1-10.
        
        Args:
            query: The user's question
            
        Returns:
            Confusion level (1-10)
        """
        try:
            system_message = """
            Analyze the following query and determine the confusion level on a scale of 1-10:
            1 = Very clear, specific question showing good understanding
            5 = Some confusion or gaps in understanding
            10 = Completely confused or lost on the topic
            
            Respond with ONLY a number between 1 and 10.
            """
            
            response = await openai_service.generate_completion(
                prompt=query,
                system_message=system_message,
                temperature=0.3,
                max_tokens=10
            )
            
            # Extract number from response
            try:
                confusion_level = int(response.strip())
                return max(1, min(10, confusion_level))  # Ensure it's between 1-10
            except ValueError:
                logger.warning(f"Could not parse confusion level: {response}")
                return 5  # Default to middle value
        except Exception as e:
            logger.error(f"Error detecting confusion level: {str(e)}")
            return 5  # Default to middle value
    
    async def get_adaptive_follow_up(self, user_id: str, query: str, response: str, confusion_level: int) -> Optional[str]:
        """Generate an adaptive follow-up based on the user's confusion level.
        
        Args:
            user_id: ID of the user
            query: The user's original question
            response: The AI's response to the question
            confusion_level: Detected confusion level (1-10)
            
        Returns:
            Adaptive follow-up question or None if not needed
        """
        # Only generate follow-up for medium to high confusion levels
        if confusion_level < 6:
            return None
        
        try:
            # Get user's learning style recommendations
            learning_style_recs = await learning_style_service.get_learning_style_recommendations(user_id)
            primary_style = learning_style_recs.get("primary_style", "balanced")
            
            # Prepare system message for follow-up generation
            system_message = f"""
            You are an AI tutor for the LEARN-X platform. The student has asked a question that indicates
            some confusion (rated {confusion_level}/10 where 10 is most confused).
            
            Their primary learning style is: {primary_style}
            
            Based on their question and your response, generate ONE follow-up question to check their understanding
            or offer additional help. The follow-up should be tailored to their learning style.
            
            Make the follow-up question short, supportive, and specific to the topic they asked about.
            """
            
            prompt = f"""
            Student's question: {query}
            
            My response: {response}
            
            Generate an appropriate follow-up question to check understanding or offer additional help.
            """
            
            follow_up = await openai_service.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7,
                max_tokens=100
            )
            
            return follow_up.strip()
        except Exception as e:
            logger.error(f"Error generating adaptive follow-up: {str(e)}")
            return None

# Create a singleton instance of the AITutoringService
ai_tutoring_service = AITutoringService()
