import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import asyncpg
import numpy as np
from prisma.models import ContentChunk, Material
from prisma.client import Prisma

from app.core.config import settings
from app.services.openai import openai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabaseService:
    """Service for interacting with pgvector database for vector embeddings and similarity search."""
    
    def __init__(self):
        """Initialize the vector database service."""
        self.db_url = settings.DATABASE_URL
        self.embedding_dimension = 1536  # OpenAI embedding dimension
        self.similarity_threshold = 0.7  # Default similarity threshold
        self.match_count = 10  # Default number of matches to return
        self.prisma = Prisma()
    
    async def connect(self) -> None:
        """Connect to the database."""
        try:
            await self.prisma.connect()
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        try:
            await self.prisma.disconnect()
            logger.info("Disconnected from database")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {str(e)}")
    
    async def ensure_pgvector_extension(self) -> bool:
        """Ensure pgvector extension is enabled in the database."""
        try:
            # Connect directly with asyncpg to run raw SQL
            conn = await asyncpg.connect(self.db_url)
            
            # Check if pgvector extension is already installed
            extension_exists = await conn.fetchval(
                """SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                )"""
            )
            
            if not extension_exists:
                # Create the extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                logger.info("pgvector extension enabled")
            else:
                logger.info("pgvector extension already enabled")
            
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"Error ensuring pgvector extension: {str(e)}")
            return False
    
    async def create_vector_index(self) -> bool:
        """Create vector index on content_chunks table if it doesn't exist."""
        try:
            # Connect directly with asyncpg to run raw SQL
            conn = await asyncpg.connect(self.db_url)
            
            # Check if the index already exists
            index_exists = await conn.fetchval(
                """SELECT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE indexname = 'content_chunks_embedding_idx'
                )"""
            )
            
            if not index_exists:
                # Create the index
                await conn.execute(
                    """CREATE INDEX content_chunks_embedding_idx 
                    ON content_chunks USING ivfflat (embedding vector_l2_ops) 
                    WITH (lists = 100);"""
                )
                logger.info("Vector index created on content_chunks table")
            else:
                logger.info("Vector index already exists on content_chunks table")
            
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating vector index: {str(e)}")
            return False
    
    async def generate_and_store_embeddings(self, content_chunk_id: str, content: str) -> bool:
        """Generate embeddings for content and store in the database."""
        try:
            # Generate embeddings using OpenAI
            embeddings = await openai_service.generate_embeddings([content])
            if not embeddings or len(embeddings) == 0:
                logger.error(f"Failed to generate embeddings for content chunk {content_chunk_id}")
                return False
            
            embedding = embeddings[0]
            
            # Connect directly with asyncpg to update the embedding
            conn = await asyncpg.connect(self.db_url)
            
            # Update the embedding in the database
            await conn.execute(
                """UPDATE content_chunks 
                SET embedding = $1::vector 
                WHERE id = $2""",
                embedding, content_chunk_id
            )
            
            await conn.close()
            logger.info(f"Embeddings stored for content chunk {content_chunk_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            return False
    
    async def batch_generate_embeddings(self, content_chunks: List[Dict[str, Any]]) -> bool:
        """Generate and store embeddings for multiple content chunks in batch."""
        try:
            if not content_chunks:
                return True
            
            # Extract content and IDs
            contents = [chunk['content'] for chunk in content_chunks]
            chunk_ids = [chunk['id'] for chunk in content_chunks]
            
            # Generate embeddings in batch
            embeddings = await openai_service.generate_embeddings(contents)
            if not embeddings or len(embeddings) != len(contents):
                logger.error(f"Failed to generate embeddings for batch content chunks")
                return False
            
            # Connect directly with asyncpg to update the embeddings
            conn = await asyncpg.connect(self.db_url)
            
            # Use a transaction for batch updates
            async with conn.transaction():
                for i, chunk_id in enumerate(chunk_ids):
                    await conn.execute(
                        """UPDATE content_chunks 
                        SET embedding = $1::vector 
                        WHERE id = $2""",
                        embeddings[i], chunk_id
                    )
            
            await conn.close()
            logger.info(f"Embeddings stored for {len(content_chunks)} content chunks")
            return True
        except Exception as e:
            logger.error(f"Error storing batch embeddings: {str(e)}")
            return False
    
    async def get_content_chunks_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get content chunks that don't have embeddings yet."""
        try:
            # Connect directly with asyncpg to run raw SQL
            conn = await asyncpg.connect(self.db_url)
            
            # Get content chunks without embeddings
            rows = await conn.fetch(
                """SELECT id, content, material_id 
                FROM content_chunks 
                WHERE embedding IS NULL 
                LIMIT $1""",
                limit
            )
            
            # Convert to list of dictionaries
            content_chunks = [
                {
                    'id': row['id'],
                    'content': row['content'],
                    'material_id': row['material_id']
                }
                for row in rows
            ]
            
            await conn.close()
            return content_chunks
        except Exception as e:
            logger.error(f"Error getting content chunks without embeddings: {str(e)}")
            return []
    
    async def similarity_search(self, query: str, similarity_threshold: float = None, match_count: int = None) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity."""
        try:
            # Use default values if not provided
            if similarity_threshold is None:
                similarity_threshold = self.similarity_threshold
            if match_count is None:
                match_count = self.match_count
            
            # Generate embedding for the query
            query_embeddings = await openai_service.generate_embeddings([query])
            if not query_embeddings or len(query_embeddings) == 0:
                logger.error("Failed to generate embeddings for query")
                return []
            
            query_embedding = query_embeddings[0]
            
            # Connect directly with asyncpg to run similarity search
            conn = await asyncpg.connect(self.db_url)
            
            # Run similarity search using the search_content_chunks function
            rows = await conn.fetch(
                """SELECT * FROM search_content_chunks($1::vector, $2, $3)""",
                query_embedding, similarity_threshold, match_count
            )
            
            # Convert to list of dictionaries
            results = [
                {
                    'id': row['id'],
                    'content': row['content'],
                    'material_id': row['material_id'],
                    'similarity': row['similarity']
                }
                for row in rows
            ]
            
            await conn.close()
            return results
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            return []
    
    async def get_material_context(self, material_id: str, context_window: int = 1) -> Dict[str, Any]:
        """Get a material and its content chunks for context."""
        try:
            # Get material details
            material = await self.prisma.material.find_unique(
                where={
                    'id': material_id
                },
                include={
                    'topic': True,
                    'contentChunks': True
                }
            )
            
            if not material:
                return None
            
            # Convert to dictionary
            material_dict = material.dict()
            
            return material_dict
        except Exception as e:
            logger.error(f"Error getting material context: {str(e)}")
            return None
    
    async def process_material_for_embeddings(self, material_id: str) -> bool:
        """Process a material's content chunks for embeddings."""
        try:
            # Get content chunks for the material
            content_chunks = await self.prisma.contentchunk.find_many(
                where={
                    'materialId': material_id
                }
            )
            
            if not content_chunks:
                logger.warning(f"No content chunks found for material {material_id}")
                return False
            
            # Convert to list of dictionaries
            chunks_data = [
                {
                    'id': chunk.id,
                    'content': chunk.content,
                    'material_id': chunk.materialId
                }
                for chunk in content_chunks
            ]
            
            # Generate and store embeddings in batch
            success = await self.batch_generate_embeddings(chunks_data)
            return success
        except Exception as e:
            logger.error(f"Error processing material for embeddings: {str(e)}")
            return False

# Create a singleton instance of the VectorDatabaseService
vector_database_service = VectorDatabaseService()
