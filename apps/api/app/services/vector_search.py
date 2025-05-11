import logging
from typing import List, Dict, Any, Optional

from app.services.vector_database import vector_database_service
from app.services.openai import openai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorSearchService:
    """Service for performing vector-based semantic search and retrieval."""
    
    def __init__(self):
        """Initialize the vector search service."""
        self.default_similarity_threshold = 0.7
        self.default_match_count = 5
    
    async def search_by_query(self, query: str, similarity_threshold: float = None, match_count: int = None) -> List[Dict[str, Any]]:
        """Search for content similar to the query.
        
        Args:
            query: The search query
            similarity_threshold: Minimum similarity threshold (0-1)
            match_count: Maximum number of matches to return
            
        Returns:
            List of matching content chunks with similarity scores
        """
        try:
            # Use default values if not provided
            if similarity_threshold is None:
                similarity_threshold = self.default_similarity_threshold
            if match_count is None:
                match_count = self.default_match_count
            
            # Perform similarity search
            results = await vector_database_service.similarity_search(
                query=query,
                similarity_threshold=similarity_threshold,
                match_count=match_count
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching by query: {str(e)}")
            return []
    
    async def get_relevant_context(self, query: str, max_chunks: int = 3) -> str:
        """Get relevant context for a query by combining the most similar content chunks.
        
        Args:
            query: The query to find context for
            max_chunks: Maximum number of chunks to include in context
            
        Returns:
            Combined context string from the most relevant chunks
        """
        try:
            # Search for similar content
            results = await self.search_by_query(
                query=query,
                match_count=max_chunks
            )
            
            if not results:
                return ""
            
            # Combine the content from the results
            context_parts = []
            for result in results:
                context_parts.append(f"Content: {result['content']}\nSimilarity: {result['similarity']:.4f}")
            
            context = "\n\n".join(context_parts)
            return context
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return ""
    
    async def answer_with_context(self, question: str, max_context_chunks: int = 3) -> Dict[str, Any]:
        """Answer a question using relevant context from vector search.
        
        Args:
            question: The question to answer
            max_context_chunks: Maximum number of context chunks to include
            
        Returns:
            Dictionary containing the answer and the context used
        """
        try:
            # Get relevant context
            context = await self.get_relevant_context(
                query=question,
                max_chunks=max_context_chunks
            )
            
            if not context:
                # No context found, generate a response without context
                answer = await openai_service.generate_completion(
                    prompt=f"Question: {question}\n\nAnswer the question based on your knowledge.",
                    system_message="You are a helpful educational assistant. Answer questions accurately and concisely."
                )
                
                return {
                    "answer": answer,
                    "context": None,
                    "has_context": False
                }
            
            # Generate an answer using the context
            answer = await openai_service.generate_completion(
                prompt=f"Question: {question}\n\nContext:\n{context}\n\nAnswer the question based on the provided context. If the context doesn't contain enough information, say so.",
                system_message="You are a helpful educational assistant. Answer questions accurately based on the provided context."
            )
            
            return {
                "answer": answer,
                "context": context,
                "has_context": True
            }
        except Exception as e:
            logger.error(f"Error answering with context: {str(e)}")
            return {
                "answer": f"I'm sorry, I encountered an error while trying to answer your question: {str(e)}",
                "context": None,
                "has_context": False,
                "error": str(e)
            }
    
    async def find_related_materials(self, query: str, max_materials: int = 5) -> List[Dict[str, Any]]:
        """Find materials related to a query based on vector similarity.
        
        Args:
            query: The search query
            max_materials: Maximum number of materials to return
            
        Returns:
            List of related materials with similarity scores
        """
        try:
            # Search for similar content chunks
            results = await self.search_by_query(
                query=query,
                match_count=max_materials * 2  # Get more chunks to find unique materials
            )
            
            if not results:
                return []
            
            # Group by material_id and get the highest similarity for each material
            materials_map = {}
            for result in results:
                material_id = result['material_id']
                similarity = result['similarity']
                
                if material_id not in materials_map or similarity > materials_map[material_id]['similarity']:
                    materials_map[material_id] = {
                        'material_id': material_id,
                        'similarity': similarity,
                        'sample_content': result['content'][:100] + '...' if len(result['content']) > 100 else result['content']
                    }
            
            # Convert to list and sort by similarity
            related_materials = list(materials_map.values())
            related_materials.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Limit to max_materials
            return related_materials[:max_materials]
        except Exception as e:
            logger.error(f"Error finding related materials: {str(e)}")
            return []

# Create a singleton instance of the VectorSearchService
vector_search_service = VectorSearchService()
