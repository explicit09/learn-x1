from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
from prisma.models import ContentChunk, Material
from app.services.openai import openai_service
from app.services.text_chunking import text_chunking_service
from app.services.prisma import prisma

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Service for managing vector embeddings for content retrieval."""
    
    async def process_material_content(self, material_id: str) -> List[str]:
        """Process material content and generate embeddings.
        
        Args:
            material_id: ID of the material to process
            
        Returns:
            List of content chunk IDs that were processed
        """
        # Get the material
        material = await prisma.material.find_unique(
            where={"id": material_id},
            include={"content_chunks": True}
        )
        
        if not material:
            logger.error(f"Material not found: {material_id}")
            return []
        
        # Delete existing chunks if any
        if material.content_chunks:
            await prisma.contentchunk.delete_many(
                where={"material_id": material_id}
            )
        
        # Chunk the content based on content type
        content = material.content
        chunks = []
        
        if material.content_type == "markdown":
            chunks = text_chunking_service.chunk_markdown(content)
        else:  # Default to plain text chunking
            chunks = text_chunking_service.chunk_text(content)
        
        # Store chunks and generate embeddings
        chunk_ids = []
        for chunk_text in chunks:
            # Create content chunk
            chunk = await prisma.contentchunk.create(
                data={
                    "content": chunk_text,
                    "material_id": material_id,
                }
            )
            chunk_ids.append(chunk.id)
            
            # Generate and store embedding
            await self.generate_embedding_for_chunk(chunk.id, chunk_text)
        
        return chunk_ids
    
    async def generate_embedding_for_chunk(self, chunk_id: str, content: str) -> bool:
        """Generate and store embedding for a content chunk.
        
        Args:
            chunk_id: ID of the content chunk
            content: Text content to generate embedding for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            embeddings = await openai_service.generate_embeddings([content])
            if not embeddings or len(embeddings) == 0:
                logger.error(f"Failed to generate embedding for chunk: {chunk_id}")
                return False
            
            embedding = embeddings[0]
            
            # Store embedding in database using pgvector
            # Convert the embedding list to a string representation for pgvector
            embedding_str = '{' + ','.join(str(x) for x in embedding) + '}'
            
            # Execute raw SQL to update the embedding
            await prisma.execute_raw(
                "UPDATE content_chunks SET embedding = $1::vector WHERE id = $2",
                [embedding_str, chunk_id]
            )
            
            # For now, we'll log that the embedding was generated
            logger.info(f"Generated embedding for chunk: {chunk_id}")
            return True
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return False
    
    async def search_similar_content(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for content similar to the query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of content chunks with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embeddings = await openai_service.generate_embeddings([query])
            if not query_embeddings or len(query_embeddings) == 0:
                logger.error("Failed to generate embedding for query")
                return []
            
            query_embedding = query_embeddings[0]
            
            # Search for similar content using pgvector
            # Convert the embedding list to a string representation for pgvector
            query_embedding_str = '{' + ','.join(str(x) for x in query_embedding) + '}'
            
            # Execute raw SQL to search for similar content
            results = await prisma.execute_raw(
                """SELECT c.id, c.content, c.material_id, m.title as material_title, 
                   1 - (c.embedding <=> $1::vector) as similarity
                   FROM content_chunks c
                   JOIN materials m ON c.material_id = m.id
                   WHERE c.embedding IS NOT NULL
                   ORDER BY c.embedding <=> $1::vector LIMIT $2
                """,
                [query_embedding_str, limit]
            )
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "id": row[0],
                    "content": row[1],
                    "material_id": row[2],
                    "title": row[3],
                    "similarity": float(row[4])
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching similar content: {str(e)}")
            return []

# Create a singleton instance of the EmbeddingsService
embeddings_service = EmbeddingsService()
