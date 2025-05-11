from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from datetime import datetime, timedelta
import re

from app.services.prisma import prisma
from app.services.openai import openai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfusionDetectionService:
    """
    Service for detecting and responding to student confusion in the LEARN-X platform.
    
    This service provides algorithms to detect confusion in student interactions,
    analyze patterns of confusion, and recommend appropriate interventions.
    """
    
    def __init__(self):
        """Initialize the confusion detection service."""
        # Confusion detection thresholds
        self.confusion_threshold = 0.7  # Threshold for classifying text as confused
        self.repeated_questions_threshold = 3  # Number of similar questions that indicate confusion
        self.response_time_threshold = 60  # Seconds spent on a question that might indicate confusion
        self.error_rate_threshold = 0.6  # Error rate in quizzes that indicates confusion
        
        # Confusion indicators and patterns
        self.confusion_indicators = [
            "I don't understand", "confused", "unclear", "not sure", "don't get it",
            "what does this mean", "lost", "struggling", "difficult to follow",
            "can you explain", "I'm stuck", "help me understand", "this doesn't make sense"
        ]
        
        # Compile regex patterns for faster matching
        self.confusion_patterns = [
            re.compile(r'\b' + re.escape(indicator) + r'\b', re.IGNORECASE)
            for indicator in self.confusion_indicators
        ]
    
    async def connect(self) -> None:
        """Connect to required services."""
        pass  # No specific connection needed
    
    async def disconnect(self) -> None:
        """Disconnect from services."""
        pass  # No specific disconnection needed
    
    async def detect_confusion_in_text(self, text: str) -> Dict[str, Any]:
        """Detect confusion signals in text using pattern matching and NLP.
        
        Args:
            text: The text to analyze for confusion signals
            
        Returns:
            Dictionary with confusion detection results
        """
        try:
            # Initialize result
            result = {
                "is_confused": False,
                "confusion_score": 0.0,
                "confusion_indicators": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Check for confusion patterns using regex
            pattern_matches = []
            for i, pattern in enumerate(self.confusion_patterns):
                if pattern.search(text):
                    pattern_matches.append(self.confusion_indicators[i])
            
            # If we have pattern matches, calculate initial score
            if pattern_matches:
                # More matches indicate higher confusion
                pattern_score = min(len(pattern_matches) / 3, 1.0)  # Cap at 1.0
                result["confusion_indicators"] = pattern_matches
                result["confusion_score"] = pattern_score
                
                # If pattern score is high enough, mark as confused
                if pattern_score >= self.confusion_threshold:
                    result["is_confused"] = True
                    return result
            
            # If no clear patterns or score is below threshold, use NLP
            # Prepare prompt for confusion detection
            system_prompt = """
            You are an AI that specializes in detecting confusion in student messages.
            Analyze the following message and determine if the student is expressing confusion.
            Rate the confusion level on a scale from 0.0 to 1.0, where:
            - 0.0 means no confusion at all
            - 1.0 means extremely confused
            
            Respond with a JSON object containing:
            - confusion_score: the numerical score (0.0 to 1.0)
            - is_confused: boolean (true if score >= 0.7, false otherwise)
            - indicators: array of phrases or words that indicate confusion
            - reasoning: brief explanation for your assessment
            """
            
            user_prompt = f"Student message: {text}"
            
            # Get NLP-based confusion assessment
            response = await openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            try:
                # Parse the JSON response
                nlp_result = json.loads(response)
                
                # Update result with NLP assessment
                result["confusion_score"] = nlp_result.get("confusion_score", 0.0)
                result["is_confused"] = nlp_result.get("is_confused", False)
                
                # Add NLP-detected indicators to our pattern matches
                nlp_indicators = nlp_result.get("indicators", [])
                if nlp_indicators:
                    result["confusion_indicators"] = list(set(result["confusion_indicators"] + nlp_indicators))
                
                # Add reasoning if available
                if "reasoning" in nlp_result:
                    result["reasoning"] = nlp_result["reasoning"]
            except json.JSONDecodeError:
                # If JSON parsing fails, fall back to pattern-based result
                logger.warning(f"Failed to parse NLP confusion detection response: {response}")
            
            return result
        except Exception as e:
            logger.error(f"Error detecting confusion in text: {str(e)}")
            return {
                "is_confused": False,
                "confusion_score": 0.0,
                "confusion_indicators": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def detect_confusion_in_interaction(self, interaction_id: str) -> Dict[str, Any]:
        """Detect confusion in a specific user interaction.
        
        Args:
            interaction_id: ID of the interaction to analyze
            
        Returns:
            Dictionary with confusion detection results
        """
        try:
            # Get the interaction
            interaction = await prisma.userinteraction.find_unique(
                where={"id": interaction_id},
                include={
                    "user": True,
                    "material": True
                }
            )
            
            if not interaction:
                return {"error": "Interaction not found"}
            
            # Initialize result
            result = {
                "interaction_id": interaction_id,
                "user_id": interaction.user.id if interaction.user else None,
                "material_id": interaction.material.id if interaction.material else None,
                "is_confused": False,
                "confusion_score": 0.0,
                "confusion_indicators": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Check for confusion based on interaction type
            if interaction.type == "QUESTION":
                # For questions, analyze the question text
                if interaction.content:
                    text_analysis = await self.detect_confusion_in_text(interaction.content)
                    result.update({
                        "is_confused": text_analysis["is_confused"],
                        "confusion_score": text_analysis["confusion_score"],
                        "confusion_indicators": text_analysis["confusion_indicators"]
                    })
            
            elif interaction.type == "QUIZ":
                # For quizzes, analyze the error rate
                if hasattr(interaction, "quiz_result") and interaction.quiz_result:
                    quiz_result = interaction.quiz_result
                    if quiz_result.possible_score > 0:
                        error_rate = 1.0 - (quiz_result.score / quiz_result.possible_score)
                        result["error_rate"] = error_rate
                        
                        # High error rate indicates confusion
                        if error_rate >= self.error_rate_threshold:
                            result["is_confused"] = True
                            result["confusion_score"] = error_rate
                            result["confusion_indicators"].append("High error rate in quiz")
            
            elif interaction.type == "VIEW":
                # For content views, check time spent and repeated views
                if hasattr(interaction, "duration") and interaction.duration:
                    # Long duration might indicate struggling with content
                    if interaction.duration > 300:  # More than 5 minutes on a single content
                        result["confusion_score"] += 0.3
                        result["confusion_indicators"].append("Extended time spent on content")
                
                # Check for repeated views of the same content
                if interaction.material:
                    repeated_views = await prisma.userinteraction.count(
                        where={
                            "userId": interaction.user.id,
                            "materialId": interaction.material.id,
                            "type": "VIEW",
                            "createdAt": {
                                "gte": datetime.now() - timedelta(days=7)  # Within last week
                            }
                        }
                    )
                    
                    if repeated_views >= 3:  # Viewing same content 3+ times might indicate confusion
                        result["confusion_score"] += 0.4
                        result["confusion_indicators"].append(f"Repeated views ({repeated_views} times)")
            
            # Update is_confused based on final score
            if result["confusion_score"] >= self.confusion_threshold:
                result["is_confused"] = True
            
            return result
        except Exception as e:
            logger.error(f"Error detecting confusion in interaction: {str(e)}")
            return {
                "interaction_id": interaction_id,
                "is_confused": False,
                "confusion_score": 0.0,
                "confusion_indicators": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_user_confusion_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze confusion patterns for a specific user over time.
        
        Args:
            user_id: ID of the user to analyze
            days: Number of days to look back
            
        Returns:
            Dictionary with confusion pattern analysis
        """
        try:
            # Get user interactions within the specified time period
            since_date = datetime.now() - timedelta(days=days)
            
            interactions = await prisma.userinteraction.find_many(
                where={
                    "userId": user_id,
                    "createdAt": {
                        "gte": since_date
                    }
                },
                include={
                    "material": {
                        "include": {
                            "topic": True
                        }
                    },
                    "quizResult": True
                },
                order_by={
                    "createdAt": "asc"
                }
            )
            
            if not interactions:
                return {
                    "user_id": user_id,
                    "confusion_level": "low",
                    "confusion_score": 0.0,
                    "confused_topics": [],
                    "confusion_trend": "stable",
                    "message": "No interactions found for analysis"
                }
            
            # Analyze interactions for confusion patterns
            confused_interactions = 0
            total_confusion_score = 0.0
            topic_confusion = {}  # Track confusion by topic
            confusion_by_week = {}  # Track confusion over time
            
            for interaction in interactions:
                # Detect confusion in this interaction
                confusion_result = await self.detect_confusion_in_interaction(interaction.id)
                
                # Update counts and scores
                if confusion_result.get("is_confused", False):
                    confused_interactions += 1
                    
                total_confusion_score += confusion_result.get("confusion_score", 0.0)
                
                # Track confusion by topic
                if interaction.material and interaction.material.topic:
                    topic_id = interaction.material.topic.id
                    topic_name = interaction.material.topic.name
                    
                    if topic_id not in topic_confusion:
                        topic_confusion[topic_id] = {
                            "id": topic_id,
                            "name": topic_name,
                            "interaction_count": 0,
                            "confusion_count": 0,
                            "average_confusion_score": 0.0
                        }
                    
                    topic_confusion[topic_id]["interaction_count"] += 1
                    
                    if confusion_result.get("is_confused", False):
                        topic_confusion[topic_id]["confusion_count"] += 1
                    
                    # Update average confusion score
                    current_total = topic_confusion[topic_id]["average_confusion_score"] * (topic_confusion[topic_id]["interaction_count"] - 1)
                    new_total = current_total + confusion_result.get("confusion_score", 0.0)
                    topic_confusion[topic_id]["average_confusion_score"] = new_total / topic_confusion[topic_id]["interaction_count"]
                
                # Track confusion over time (by week)
                week_key = interaction.createdAt.strftime("%Y-%U")  # Year and week number
                
                if week_key not in confusion_by_week:
                    confusion_by_week[week_key] = {
                        "week": week_key,
                        "interaction_count": 0,
                        "confusion_count": 0,
                        "average_confusion_score": 0.0
                    }
                
                confusion_by_week[week_key]["interaction_count"] += 1
                
                if confusion_result.get("is_confused", False):
                    confusion_by_week[week_key]["confusion_count"] += 1
                
                # Update average confusion score for the week
                current_total = confusion_by_week[week_key]["average_confusion_score"] * (confusion_by_week[week_key]["interaction_count"] - 1)
                new_total = current_total + confusion_result.get("confusion_score", 0.0)
                confusion_by_week[week_key]["average_confusion_score"] = new_total / confusion_by_week[week_key]["interaction_count"]
            
            # Calculate overall confusion metrics
            overall_confusion_score = total_confusion_score / len(interactions) if interactions else 0.0
            confusion_rate = confused_interactions / len(interactions) if interactions else 0.0
            
            # Determine overall confusion level
            confusion_level = "low"
            if confusion_rate >= 0.5 or overall_confusion_score >= 0.6:
                confusion_level = "high"
            elif confusion_rate >= 0.3 or overall_confusion_score >= 0.4:
                confusion_level = "medium"
            
            # Identify confused topics (topics with high confusion scores)
            confused_topics = []
            for topic_data in topic_confusion.values():
                if topic_data["average_confusion_score"] >= 0.5 or (topic_data["confusion_count"] / topic_data["interaction_count"] >= 0.4):
                    confused_topics.append({
                        "id": topic_data["id"],
                        "name": topic_data["name"],
                        "confusion_score": topic_data["average_confusion_score"],
                        "confusion_rate": topic_data["confusion_count"] / topic_data["interaction_count"]
                    })
            
            # Sort confused topics by confusion score (descending)
            confused_topics.sort(key=lambda x: x["confusion_score"], reverse=True)
            
            # Analyze confusion trend over time
            confusion_trend = "stable"
            if len(confusion_by_week) >= 2:
                # Convert to list and sort by week
                weeks_list = list(confusion_by_week.values())
                weeks_list.sort(key=lambda x: x["week"])
                
                # Compare first and last weeks
                first_week = weeks_list[0]
                last_week = weeks_list[-1]
                
                if last_week["average_confusion_score"] > first_week["average_confusion_score"] * 1.2:
                    confusion_trend = "increasing"
                elif last_week["average_confusion_score"] < first_week["average_confusion_score"] * 0.8:
                    confusion_trend = "decreasing"
            
            return {
                "user_id": user_id,
                "analysis_period_days": days,
                "total_interactions": len(interactions),
                "confused_interactions": confused_interactions,
                "confusion_rate": confusion_rate,
                "overall_confusion_score": overall_confusion_score,
                "confusion_level": confusion_level,
                "confused_topics": confused_topics,
                "confusion_trend": confusion_trend,
                "confusion_by_week": list(confusion_by_week.values()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing user confusion patterns: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_intervention_recommendations(self, user_id: str, topic_id: Optional[str] = None) -> Dict[str, Any]:
        """Get personalized intervention recommendations for a confused user.
        
        Args:
            user_id: ID of the user
            topic_id: Optional topic ID to focus on
            
        Returns:
            Dictionary with intervention recommendations
        """
        try:
            # Analyze user confusion patterns
            confusion_analysis = await self.analyze_user_confusion_patterns(user_id)
            
            # If user isn't confused, return minimal recommendations
            if confusion_analysis.get("confusion_level") == "low" and not topic_id:
                return {
                    "user_id": user_id,
                    "confusion_level": "low",
                    "needs_intervention": False,
                    "recommendations": [
                        "Continue with regular learning path",
                        "No specific interventions needed at this time"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get user's learning style for personalized recommendations
            learning_style = await prisma.learningstyle.find_unique(
                where={"userId": user_id}
            )
            
            # Get user's recent interactions
            recent_interactions = await prisma.userinteraction.find_many(
                where={
                    "userId": user_id,
                    "materialId": {
                        "not": None
                    },
                    "createdAt": {
                        "gte": datetime.now() - timedelta(days=30)
                    }
                },
                include={
                    "material": {
                        "include": {
                            "topic": True
                        }
                    }
                },
                order_by={
                    "createdAt": "desc"
                },
                take=20
            )
            
            # Determine topics to focus on
            focus_topics = []
            
            if topic_id:
                # If specific topic provided, focus on that
                topic = await prisma.topic.find_unique(
                    where={"id": topic_id}
                )
                if topic:
                    focus_topics.append({
                        "id": topic.id,
                        "name": topic.name
                    })
            else:
                # Otherwise use confused topics from analysis
                focus_topics = confusion_analysis.get("confused_topics", [])
            
            # If no focus topics identified, use recent interaction topics
            if not focus_topics and recent_interactions:
                topic_counts = {}
                for interaction in recent_interactions:
                    if interaction.material and interaction.material.topic:
                        topic_id = interaction.material.topic.id
                        topic_name = interaction.material.topic.name
                        
                        if topic_id not in topic_counts:
                            topic_counts[topic_id] = {
                                "id": topic_id,
                                "name": topic_name,
                                "count": 0
                            }
                        
                        topic_counts[topic_id]["count"] += 1
                
                # Sort by interaction count and take top 2
                sorted_topics = sorted(topic_counts.values(), key=lambda x: x["count"], reverse=True)
                focus_topics = [{
                    "id": topic["id"],
                    "name": topic["name"]
                } for topic in sorted_topics[:2]]
            
            # Generate personalized intervention recommendations
            recommendations = []
            resource_recommendations = []
            
            # Add general recommendations based on confusion level
            confusion_level = confusion_analysis.get("confusion_level", "medium")
            
            if confusion_level == "high":
                recommendations.append("Schedule a one-on-one tutoring session")
                recommendations.append("Consider reviewing prerequisite materials")
            elif confusion_level == "medium":
                recommendations.append("Review key concepts with additional examples")
                recommendations.append("Try alternative learning formats")
            
            # Add learning style specific recommendations
            if learning_style:
                # Determine primary learning style
                styles = [
                    ("visual", learning_style.visual_score),
                    ("auditory", learning_style.auditory_score),
                    ("reading", learning_style.reading_score),
                    ("kinesthetic", learning_style.kinesthetic_score)
                ]
                primary_style = max(styles, key=lambda x: x[1])[0]
                
                if primary_style == "visual":
                    recommendations.append("Use visual aids like diagrams and charts")
                    recommendations.append("Watch video explanations of difficult concepts")
                elif primary_style == "auditory":
                    recommendations.append("Listen to audio explanations or lectures")
                    recommendations.append("Discuss concepts with peers or tutors")
                elif primary_style == "reading":
                    recommendations.append("Read alternative textual explanations")
                    recommendations.append("Take detailed notes on difficult concepts")
                elif primary_style == "kinesthetic":
                    recommendations.append("Try hands-on exercises and practical applications")
                    recommendations.append("Use interactive simulations or exercises")
            
            # Find alternative learning resources for focus topics
            for topic in focus_topics:
                # Find materials for this topic
                topic_materials = await prisma.material.find_many(
                    where={
                        "topicId": topic["id"],
                        "status": "PUBLISHED"
                    },
                    take=5
                )
                
                if topic_materials:
                    for material in topic_materials:
                        resource_recommendations.append({
                            "id": material.id,
                            "title": material.title,
                            "type": material.type,
                            "topic_name": topic["name"],
                            "reason": f"Alternative resource for {topic['name']}"
                        })
            
            # Determine if intervention is needed
            needs_intervention = confusion_level in ["medium", "high"] or len(focus_topics) > 0
            
            return {
                "user_id": user_id,
                "confusion_level": confusion_level,
                "focus_topics": focus_topics,
                "needs_intervention": needs_intervention,
                "recommendations": recommendations,
                "resource_recommendations": resource_recommendations[:5],  # Limit to top 5
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting intervention recommendations: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def detect_class_confusion_hotspots(self, organization_id: str, days: int = 30) -> Dict[str, Any]:
        """Detect confusion hotspots across an entire class or organization.
        
        Args:
            organization_id: ID of the organization
            days: Number of days to look back
            
        Returns:
            Dictionary with confusion hotspots analysis
        """
        try:
            # Get all users in the organization
            users = await prisma.user.find_many(
                where={
                    "organizationId": organization_id,
                    "role": "STUDENT"  # Only analyze students
                }
            )
            
            if not users:
                return {
                    "organization_id": organization_id,
                    "hotspots": [],
                    "confused_users": [],
                    "message": "No users found in organization"
                }
            
            # Analyze confusion patterns for each user
            user_analyses = []
            for user in users:
                analysis = await self.analyze_user_confusion_patterns(user.id, days)
                if not "error" in analysis:
                    user_analyses.append({
                        "user_id": user.id,
                        "name": f"{user.first_name} {user.last_name}",
                        "confusion_level": analysis.get("confusion_level", "low"),
                        "confusion_score": analysis.get("overall_confusion_score", 0.0),
                        "confused_topics": analysis.get("confused_topics", [])
                    })
            
            # Identify confused users
            confused_users = [u for u in user_analyses if u["confusion_level"] in ["medium", "high"]]
            
            # Aggregate topic confusion across all users
            topic_confusion = {}
            
            for user_analysis in user_analyses:
                for topic in user_analysis.get("confused_topics", []):
                    topic_id = topic["id"]
                    
                    if topic_id not in topic_confusion:
                        topic_confusion[topic_id] = {
                            "id": topic_id,
                            "name": topic["name"],
                            "confused_user_count": 0,
                            "average_confusion_score": 0.0,
                            "confusion_scores": []
                        }
                    
                    topic_confusion[topic_id]["confused_user_count"] += 1
                    topic_confusion[topic_id]["confusion_scores"].append(topic["confusion_score"])
            
            # Calculate average confusion scores for topics
            for topic_id, data in topic_confusion.items():
                if data["confusion_scores"]:
                    data["average_confusion_score"] = sum(data["confusion_scores"]) / len(data["confusion_scores"])
                    data["confusion_rate"] = data["confused_user_count"] / len(users)
                    # Remove the raw scores list
                    del data["confusion_scores"]
            
            # Identify hotspots (topics with high confusion across multiple users)
            hotspots = []
            for topic_data in topic_confusion.values():
                # Consider it a hotspot if multiple users are confused or confusion rate is high
                if topic_data["confused_user_count"] >= 3 or topic_data["confusion_rate"] >= 0.2:
                    hotspots.append(topic_data)
            
            # Sort hotspots by confused user count (descending)
            hotspots.sort(key=lambda x: x["confused_user_count"], reverse=True)
            
            return {
                "organization_id": organization_id,
                "analysis_period_days": days,
                "total_users": len(users),
                "confused_user_count": len(confused_users),
                "confusion_rate": len(confused_users) / len(users) if users else 0.0,
                "hotspots": hotspots,
                "confused_users": confused_users,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error detecting class confusion hotspots: {str(e)}")
            return {
                "organization_id": organization_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create a singleton instance
confusion_detection_service = ConfusionDetectionService()
