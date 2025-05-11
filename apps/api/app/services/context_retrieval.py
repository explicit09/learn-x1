from typing import List, Dict, Any, Optional, Tuple
import logging
import asyncio
from datetime import datetime

from app.services.prisma import prisma
from app.services.vector_database import vector_database_service
from app.services.vector_search import vector_search_service
from app.services.openai import openai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextRetrievalService:
    """
    Service for retrieving relevant context from the vector database.
    
    This service provides advanced context retrieval capabilities including:
    - Multi-query retrieval for complex questions
    - Hybrid search combining vector and keyword search
    - Context ranking and filtering
    - Context window management
    - User-specific context retrieval based on learning history
    """
    
    def __init__(self):
        """Initialize the context retrieval service."""
        self.default_similarity_threshold = 0.7
        self.default_match_count = 5
        self.max_context_window = 4000  # Maximum number of tokens for context
        self.min_context_chunks = 3  # Minimum number of chunks to retrieve
        self.max_context_chunks = 10  # Maximum number of chunks to retrieve
        
    async def connect(self) -> None:
        """Connect to required services."""
        await vector_database_service.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from services."""
        await vector_database_service.disconnect()
    
    async def retrieve_context(self, 
                              query: str, 
                              user_id: Optional[str] = None, 
                              material_id: Optional[str] = None,
                              topic_id: Optional[str] = None,
                              similarity_threshold: Optional[float] = None,
                              match_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query.
        
        Args:
            query: The user's query
            user_id: Optional user ID for personalized context
            material_id: Optional material ID to limit context to a specific material
            topic_id: Optional topic ID to limit context to a specific topic
            similarity_threshold: Minimum similarity threshold (0-1)
            match_count: Maximum number of matches to return
            
        Returns:
            List of context chunks with similarity scores
        """
        try:
            # Use default values if not provided
            if similarity_threshold is None:
                similarity_threshold = self.default_similarity_threshold
            if match_count is None:
                match_count = self.default_match_count
            
            # Generate query embedding
            query_embedding = await openai_service.create_embedding(query)
            
            # Build the search query
            search_params = {
                "embedding": query_embedding,
                "similarity_threshold": similarity_threshold,
                "match_count": match_count
            }
            
            # Add filters if provided
            filters = {}
            if material_id:
                filters["materialId"] = material_id
            if topic_id:
                # Get materials for the topic
                materials = await prisma.material.find_many(
                    where={"topicId": topic_id}
                )
                material_ids = [m.id for m in materials]
                if material_ids:
                    filters["materialId"] = {"in": material_ids}
            
            if filters:
                search_params["filters"] = filters
            
            # Perform the search
            results = await vector_database_service.similarity_search_with_filters(**search_params)
            
            # If user_id is provided, personalize the results
            if user_id and results:
                results = await self._personalize_results(results, user_id)
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    async def retrieve_multi_query_context(self, 
                                          main_query: str, 
                                          sub_queries: List[str],
                                          user_id: Optional[str] = None,
                                          match_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve context using multiple queries for complex questions.
        
        Args:
            main_query: The main user query
            sub_queries: List of sub-queries derived from the main query
            user_id: Optional user ID for personalized context
            match_count: Maximum number of matches to return per query
            
        Returns:
            Combined and deduplicated list of context chunks
        """
        try:
            if match_count is None:
                match_count = self.default_match_count
            
            # Create tasks for all queries
            tasks = [self.retrieve_context(main_query, user_id=user_id, match_count=match_count)]
            for sub_query in sub_queries:
                tasks.append(self.retrieve_context(sub_query, user_id=user_id, match_count=match_count))
            
            # Execute all tasks concurrently
            all_results = await asyncio.gather(*tasks)
            
            # Combine and deduplicate results
            combined_results = []
            seen_ids = set()
            
            # Process main query results first
            for result in all_results[0]:
                if result["id"] not in seen_ids:
                    seen_ids.add(result["id"])
                    combined_results.append(result)
            
            # Process sub-query results
            for results in all_results[1:]:
                for result in results:
                    if result["id"] not in seen_ids:
                        seen_ids.add(result["id"])
                        combined_results.append(result)
            
            # Sort by similarity
            combined_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Limit to max_context_chunks
            return combined_results[:self.max_context_chunks]
        except Exception as e:
            logger.error(f"Error retrieving multi-query context: {str(e)}")
            return []
    
    async def generate_sub_queries(self, main_query: str) -> List[str]:
        """Generate sub-queries for a complex main query.
        
        Args:
            main_query: The main user query
            
        Returns:
            List of sub-queries
        """
        try:
            system_prompt = """
            You are an AI assistant that helps break down complex questions into simpler sub-questions.
            Your task is to analyze the main question and generate 2-3 simpler sub-questions that would help answer the main question.
            Only generate sub-questions that are directly relevant to answering the main question.
            Return ONLY the sub-questions, one per line, with no additional text or explanation.
            """
            
            user_prompt = f"Main question: {main_query}\n\nGenerate 2-3 sub-questions:"
            
            response = await openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            # Parse the response to get sub-queries
            sub_queries_text = response.strip()
            sub_queries = [q.strip() for q in sub_queries_text.split('\n') if q.strip()]
            
            return sub_queries[:3]  # Limit to 3 sub-queries
        except Exception as e:
            logger.error(f"Error generating sub-queries: {str(e)}")
            return []
    
    async def retrieve_hybrid_context(self, 
                                     query: str, 
                                     user_id: Optional[str] = None,
                                     match_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve context using hybrid search (vector + keyword).
        
        Args:
            query: The user's query
            user_id: Optional user ID for personalized context
            match_count: Maximum number of matches to return
            
        Returns:
            Combined list of context chunks from both search methods
        """
        try:
            if match_count is None:
                match_count = self.default_match_count
            
            # Perform vector search
            vector_results = await self.retrieve_context(
                query=query, 
                user_id=user_id, 
                match_count=match_count
            )
            
            # Perform keyword search
            keyword_results = await self._keyword_search(
                query=query,
                match_count=match_count
            )
            
            # Combine and deduplicate results
            combined_results = []
            seen_ids = set()
            
            # Process vector results first (they're usually more relevant)
            for result in vector_results:
                if result["id"] not in seen_ids:
                    seen_ids.add(result["id"])
                    combined_results.append(result)
            
            # Process keyword results
            for result in keyword_results:
                if result["id"] not in seen_ids:
                    seen_ids.add(result["id"])
                    # Add a default similarity score for keyword results
                    if "similarity" not in result:
                        result["similarity"] = 0.5
                    combined_results.append(result)
            
            # Sort by similarity
            combined_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Limit to max_context_chunks
            return combined_results[:self.max_context_chunks]
        except Exception as e:
            logger.error(f"Error retrieving hybrid context: {str(e)}")
            return []
    
    async def _keyword_search(self, query: str, match_count: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword-based search on content chunks.
        
        Args:
            query: The search query
            match_count: Maximum number of matches to return
            
        Returns:
            List of matching content chunks
        """
        try:
            # Extract keywords from the query
            keywords = query.lower().split()
            keywords = [k for k in keywords if len(k) > 3]  # Filter out short words
            
            if not keywords:
                return []
            
            # Build the SQL query for keyword search
            sql_query = """
            SELECT id, content, material_id
            FROM content_chunks
            WHERE 
            """
            
            conditions = []
            for keyword in keywords:
                conditions.append(f"LOWER(content) LIKE '%{keyword}%'")
            
            sql_query += " OR ".join(conditions)
            sql_query += f" LIMIT {match_count}"
            
            # Execute the query
            results = await prisma.execute_raw(sql_query)
            
            # Format the results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "id": row[0],
                    "content": row[1],
                    "material_id": row[2],
                    "search_type": "keyword"
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error performing keyword search: {str(e)}")
            return []
    
    async def _personalize_results(self, results: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Personalize search results based on user's learning history.
        
        Args:
            results: List of search results
            user_id: User ID for personalization
            
        Returns:
            Reranked list of results
        """
        try:
            # Get user's learning history and preferences
            user_history = await self._get_user_learning_history(user_id)
            user_preferences = await self._get_user_preferences(user_id)
            
            if not user_history and not user_preferences:
                return results  # No personalization data available
            
            # Calculate personalization scores for each result
            for result in results:
                personalization_score = 0.0
                
                # Check if the material is in the user's history
                material_id = result.get("material_id")
                if material_id and material_id in user_history:
                    # Boost score based on interaction count and recency
                    history_entry = user_history[material_id]
                    interaction_score = min(history_entry["interaction_count"] / 10.0, 0.5)  # Cap at 0.5
                    personalization_score += interaction_score
                
                # Apply user preferences
                if user_preferences:
                    # Example: boost score based on preferred learning style
                    if "learning_style" in user_preferences:
                        # This would require content to be tagged with learning style metadata
                        # For now, we'll just add a small boost
                        personalization_score += 0.1
                
                # Adjust the similarity score with personalization
                # We'll use a weighted combination (70% similarity, 30% personalization)
                original_similarity = result.get("similarity", 0.0)
                adjusted_similarity = (original_similarity * 0.7) + (personalization_score * 0.3)
                result["similarity"] = min(adjusted_similarity, 1.0)  # Cap at 1.0
                result["personalized"] = True
            
            # Re-sort by adjusted similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return results
        except Exception as e:
            logger.error(f"Error personalizing results: {str(e)}")
            return results  # Return original results on error
    
    async def _get_user_learning_history(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get user's learning history.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary mapping material IDs to history data
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
                take=100  # Limit to recent interactions
            )
            
            # Organize by material ID
            history = {}
            for interaction in interactions:
                material_id = interaction.material_id
                if material_id not in history:
                    history[material_id] = {
                        "interaction_count": 0,
                        "last_interaction": None,
                        "completed": False
                    }
                
                history[material_id]["interaction_count"] += 1
                
                # Update last interaction time
                if not history[material_id]["last_interaction"] or \
                   interaction.created_at > history[material_id]["last_interaction"]:
                    history[material_id]["last_interaction"] = interaction.created_at
                
                # Check if material was completed
                if interaction.type == "COMPLETE":
                    history[material_id]["completed"] = True
            
            return history
        except Exception as e:
            logger.error(f"Error getting user learning history: {str(e)}")
            return {}
    
    async def _get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's preferences for personalization.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of user preferences or None if not found
        """
        try:
            # Get user's learning style
            learning_style = await prisma.learningstyle.find_unique(
                where={"userId": user_id}
            )
            
            # Get user preferences
            user_preferences = await prisma.userpreference.find_unique(
                where={"userId": user_id}
            )
            
            if not learning_style and not user_preferences:
                return None
            
            preferences = {}
            
            # Add learning style data if available
            if learning_style:
                preferences["learning_style"] = {
                    "visual_score": learning_style.visual_score,
                    "auditory_score": learning_style.auditory_score,
                    "reading_score": learning_style.reading_score,
                    "kinesthetic_score": learning_style.kinesthetic_score
                }
                
                # Determine primary learning style
                scores = [
                    ("visual", learning_style.visual_score),
                    ("auditory", learning_style.auditory_score),
                    ("reading", learning_style.reading_score),
                    ("kinesthetic", learning_style.kinesthetic_score)
                ]
                primary_style = max(scores, key=lambda x: x[1])[0]
                preferences["primary_learning_style"] = primary_style
            
            # Add user preferences if available
            if user_preferences:
                if user_preferences.interests:
                    preferences["interests"] = user_preferences.interests
                if user_preferences.ui_preferences:
                    preferences["ui_preferences"] = user_preferences.ui_preferences
            
            return preferences
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return None
    
    async def format_context_for_llm(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Format context chunks for use in an LLM prompt.
        
        Args:
            context_chunks: List of context chunks
            
        Returns:
            Formatted context string
        """
        if not context_chunks:
            return ""
        
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks):
            content = chunk.get("content", "")
            similarity = chunk.get("similarity", 0.0)
            material_id = chunk.get("material_id", "unknown")
            
            # Get material title if available
            material_title = "Unknown Material"
            try:
                material = await prisma.material.find_unique(
                    where={"id": material_id}
                )
                if material:
                    material_title = material.title
            except Exception:
                pass
            
            formatted_chunk = f"[Context {i+1}] From: {material_title}\n{content}\n"
            formatted_chunks.append(formatted_chunk)
        
        return "\n\n".join(formatted_chunks)
    
    async def get_context_for_question(self, question: str, user_id: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """Get formatted context for a question, optimized for LLM use.
        
        Args:
            question: The user's question
            user_id: Optional user ID for personalized context
            
        Returns:
            Tuple of (formatted_context, raw_context_chunks)
        """
        try:
            # Check if this is a complex question that needs sub-queries
            is_complex = await self._is_complex_question(question)
            
            if is_complex:
                # Generate sub-queries
                sub_queries = await self.generate_sub_queries(question)
                
                # Retrieve context using multi-query approach
                context_chunks = await self.retrieve_multi_query_context(
                    main_query=question,
                    sub_queries=sub_queries,
                    user_id=user_id
                )
            else:
                # Use hybrid search for simple questions
                context_chunks = await self.retrieve_hybrid_context(
                    query=question,
                    user_id=user_id
                )
            
            # Format the context for LLM use
            formatted_context = await self.format_context_for_llm(context_chunks)
            
            return formatted_context, context_chunks
        except Exception as e:
            logger.error(f"Error getting context for question: {str(e)}")
            return "", []
    
    async def _is_complex_question(self, question: str) -> bool:
        """Determine if a question is complex and needs sub-queries.
        
        Args:
            question: The user's question
            
        Returns:
            True if the question is complex, False otherwise
        """
        # Simple heuristic: check question length and presence of multiple question marks
        if len(question.split()) > 15 or question.count("?") > 1:
            return True
        
        # Check for complex question indicators
        complex_indicators = [
            "compare", "contrast", "difference", "similarities", "advantages", "disadvantages",
            "pros and cons", "explain how", "why does", "how does", "what are the steps",
            "what is the relationship", "how would you", "analyze", "evaluate"
        ]
        
        question_lower = question.lower()
        for indicator in complex_indicators:
            if indicator in question_lower:
                return True
        
        return False

# Create a singleton instance
context_retrieval_service = ContextRetrievalService()
