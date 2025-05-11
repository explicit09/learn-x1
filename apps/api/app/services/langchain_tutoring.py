import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.services.vector_database import vector_database_service
from app.services.vector_search import vector_search_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainTutoringService:
    """Service for AI tutoring using LangChain."""
    
    def __init__(self):
        """Initialize the LangChain tutoring service."""
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OpenAI API key not found. AI tutoring will not work.")
        
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.temperature = 0.7
        self.max_tokens = 1000
        
        # Initialize OpenAI chat model
        self.chat_model = ChatOpenAI(
            api_key=self.api_key,
            model_name=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=self.api_key,
            model=self.embedding_model
        )
        
        # System prompts for different tutoring modes
        self.system_prompts = {
            "default": "You are an AI tutor for the LEARN-X educational platform. Your goal is to help students understand concepts and answer their questions accurately and clearly. Use the provided context to inform your responses.",
            "beginner": "You are an AI tutor for the LEARN-X educational platform, specializing in helping beginners. Explain concepts in simple terms, using analogies and examples. Avoid technical jargon unless necessary, and when used, explain it clearly. Use the provided context to inform your responses.",
            "advanced": "You are an AI tutor for the LEARN-X educational platform, specializing in advanced topics. Provide detailed, technical explanations and challenge the student to think critically. Use the provided context to inform your responses.",
            "socratic": "You are an AI tutor for the LEARN-X educational platform, using the Socratic method. Guide students to discover answers through thoughtful questions rather than providing direct answers. Use the provided context to inform your responses."
        }
    
    async def _get_relevant_context(self, query: str, max_chunks: int = 3) -> str:
        """Get relevant context for a query using vector search."""
        try:
            # Use vector search service to get relevant context
            context = await vector_search_service.get_relevant_context(
                query=query,
                max_chunks=max_chunks
            )
            return context
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return ""
    
    async def answer_question(self, 
                             question: str, 
                             chat_history: List[Dict[str, str]] = None, 
                             tutoring_mode: str = "default",
                             user_id: str = None,
                             course_id: str = None,
                             confusion_level: int = None) -> Dict[str, Any]:
        """Answer a question using LangChain and vector search for context.
        
        Args:
            question: The question to answer
            chat_history: Previous messages in the conversation
            tutoring_mode: Mode of tutoring (default, beginner, advanced, socratic)
            user_id: ID of the user asking the question
            course_id: ID of the course the question is related to
            confusion_level: Level of confusion (1-10) expressed by the user
            
        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            # Get system prompt based on tutoring mode
            system_prompt = self.system_prompts.get(tutoring_mode, self.system_prompts["default"])
            
            # Add confusion level context if provided
            if confusion_level is not None:
                if confusion_level >= 7:
                    system_prompt += " The student seems very confused. Provide a simpler explanation and break down concepts into smaller parts."
                elif confusion_level >= 4:
                    system_prompt += " The student seems somewhat confused. Clarify your explanations and provide examples."
            
            # Get relevant context for the question
            context = await self._get_relevant_context(question)
            
            # Convert chat history to LangChain message format
            messages = [SystemMessage(content=system_prompt)]
            if chat_history:
                for message in chat_history:
                    if message["role"] == "user":
                        messages.append(HumanMessage(content=message["content"]))
                    elif message["role"] == "assistant":
                        messages.append(AIMessage(content=message["content"]))
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("system", "Context information for the question:\n{context}"),
                ("human", "{question}")
            ])
            
            # Create chain
            chain = prompt | self.chat_model | StrOutputParser()
            
            # Run chain
            answer = await chain.ainvoke({
                "chat_history": messages[1:],  # Exclude system message
                "context": context,
                "question": question
            })
            
            # Prepare response
            response = {
                "answer": answer,
                "has_context": bool(context),
                "tutoring_mode": tutoring_mode,
                "timestamp": datetime.now().isoformat()
            }
            
            return response
        except Exception as e:
            logger.error(f"Error answering question with LangChain: {str(e)}")
            return {
                "answer": f"I'm sorry, I encountered an error while trying to answer your question: {str(e)}",
                "has_context": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def explain_concept(self, 
                             concept: str, 
                             detail_level: str = "medium",
                             user_id: str = None,
                             course_id: str = None) -> Dict[str, Any]:
        """Explain a concept using LangChain and vector search for context.
        
        Args:
            concept: The concept to explain
            detail_level: Level of detail (basic, medium, advanced)
            user_id: ID of the user requesting the explanation
            course_id: ID of the course the concept is related to
            
        Returns:
            Dictionary containing the explanation and metadata
        """
        try:
            # Map detail level to tutoring mode
            detail_to_mode = {
                "basic": "beginner",
                "medium": "default",
                "advanced": "advanced"
            }
            tutoring_mode = detail_to_mode.get(detail_level, "default")
            
            # Get system prompt based on tutoring mode
            system_prompt = self.system_prompts.get(tutoring_mode, self.system_prompts["default"])
            system_prompt += f" Explain the concept of '{concept}' at a {detail_level} level of detail."
            
            # Get relevant context for the concept
            context = await self._get_relevant_context(concept)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("system", "Context information for the concept:\n{context}"),
                ("human", f"Please explain the concept of {concept}")
            ])
            
            # Create chain
            chain = prompt | self.chat_model | StrOutputParser()
            
            # Run chain
            explanation = await chain.ainvoke({
                "context": context
            })
            
            # Prepare response
            response = {
                "concept": concept,
                "explanation": explanation,
                "detail_level": detail_level,
                "has_context": bool(context),
                "timestamp": datetime.now().isoformat()
            }
            
            return response
        except Exception as e:
            logger.error(f"Error explaining concept with LangChain: {str(e)}")
            return {
                "concept": concept,
                "explanation": f"I'm sorry, I encountered an error while trying to explain this concept: {str(e)}",
                "has_context": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_study_plan(self,
                                topic: str,
                                learning_goal: str,
                                duration_days: int = 7,
                                user_id: str = None,
                                course_id: str = None) -> Dict[str, Any]:
        """Generate a personalized study plan for a topic.
        
        Args:
            topic: The topic to create a study plan for
            learning_goal: The learning goal or objective
            duration_days: Duration of the study plan in days
            user_id: ID of the user requesting the study plan
            course_id: ID of the course the topic is related to
            
        Returns:
            Dictionary containing the study plan and metadata
        """
        try:
            # Create system prompt for study plan generation
            system_prompt = f"""You are an AI tutor for the LEARN-X educational platform. 
            Create a {duration_days}-day study plan for the topic '{topic}' with the learning goal: '{learning_goal}'.
            The study plan should be structured, progressive, and include specific activities for each day.
            Include recommended resources, practice exercises, and self-assessment methods."""
            
            # Get relevant context for the topic
            context = await self._get_relevant_context(f"{topic} {learning_goal}")
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("system", "Context information for the topic:\n{context}"),
                ("human", f"Please create a {duration_days}-day study plan for {topic} to achieve the goal: {learning_goal}")
            ])
            
            # Create chain
            chain = prompt | self.chat_model | StrOutputParser()
            
            # Run chain
            study_plan = await chain.ainvoke({
                "context": context
            })
            
            # Prepare response
            response = {
                "topic": topic,
                "learning_goal": learning_goal,
                "duration_days": duration_days,
                "study_plan": study_plan,
                "has_context": bool(context),
                "timestamp": datetime.now().isoformat()
            }
            
            return response
        except Exception as e:
            logger.error(f"Error generating study plan with LangChain: {str(e)}")
            return {
                "topic": topic,
                "learning_goal": learning_goal,
                "study_plan": f"I'm sorry, I encountered an error while trying to generate a study plan: {str(e)}",
                "has_context": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def assess_answer(self,
                          question: str,
                          student_answer: str,
                          user_id: str = None,
                          course_id: str = None) -> Dict[str, Any]:
        """Assess a student's answer to a question.
        
        Args:
            question: The question that was asked
            student_answer: The student's answer to assess
            user_id: ID of the user whose answer is being assessed
            course_id: ID of the course the question is related to
            
        Returns:
            Dictionary containing the assessment and metadata
        """
        try:
            # Create system prompt for answer assessment
            system_prompt = """You are an AI tutor for the LEARN-X educational platform. 
            Assess the student's answer to the given question. 
            Provide constructive feedback, pointing out strengths and areas for improvement.
            Include a correctness score from 0-100 and specific suggestions for improvement.
            Format your response with clear sections for Feedback, Score, and Suggestions."""
            
            # Get relevant context for the question
            context = await self._get_relevant_context(question)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("system", "Context information for the question:\n{context}"),
                ("human", f"Question: {question}\n\nStudent's Answer: {student_answer}\n\nPlease assess this answer.")
            ])
            
            # Create chain
            chain = prompt | self.chat_model | StrOutputParser()
            
            # Run chain
            assessment = await chain.ainvoke({
                "context": context
            })
            
            # Prepare response
            response = {
                "question": question,
                "student_answer": student_answer,
                "assessment": assessment,
                "has_context": bool(context),
                "timestamp": datetime.now().isoformat()
            }
            
            return response
        except Exception as e:
            logger.error(f"Error assessing answer with LangChain: {str(e)}")
            return {
                "question": question,
                "student_answer": student_answer,
                "assessment": f"I'm sorry, I encountered an error while trying to assess this answer: {str(e)}",
                "has_context": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create a singleton instance of the LangChainTutoringService
langchain_tutoring_service = LangChainTutoringService()
