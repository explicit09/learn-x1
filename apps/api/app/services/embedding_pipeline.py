import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
import time
from datetime import datetime, timedelta

from app.core.config import settings
from app.services.vector_database import vector_database_service
from app.services.content_chunking import content_chunking_service
from app.services.openai import openai_service
from app.services.prisma import prisma

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingPipelineService:
    """Service for managing the embedding generation pipeline.
    
    This service coordinates the process of:
    1. Identifying materials that need embeddings
    2. Chunking content into appropriate sizes
    3. Generating embeddings using OpenAI
    4. Storing embeddings in the vector database
    5. Tracking embedding status and metrics
    """
    
    def __init__(self):
        """Initialize the embedding pipeline service."""
        # Configuration settings
        self.batch_size = 50  # Number of chunks to process in a batch
        self.rate_limit_delay = 0.5  # Delay between API calls to avoid rate limiting
        self.max_retries = 3  # Maximum number of retries for failed operations
        self.retry_delay = 2  # Delay between retries in seconds
        
        # Metrics tracking
        self.metrics = {
            "materials_processed": 0,
            "chunks_processed": 0,
            "embeddings_generated": 0,
            "failed_embeddings": 0,
            "total_tokens": 0,
            "total_processing_time": 0,
            "last_run": None,
        }
    
    async def connect(self) -> bool:
        """Connect to required services."""
        try:
            # Connect to the database
            await vector_database_service.connect()
            
            # Ensure pgvector extension is enabled
            extension_enabled = await vector_database_service.ensure_pgvector_extension()
            if not extension_enabled:
                logger.error("Failed to enable pgvector extension")
                return False
            
            # Create vector index if it doesn't exist
            index_created = await vector_database_service.create_vector_index()
            if not index_created:
                logger.error("Failed to create vector index")
                return False
            
            # Connect content chunking service
            await content_chunking_service.connect()
            
            logger.info("Successfully connected to all required services")
            return True
        except Exception as e:
            logger.error(f"Error connecting to services: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from all services."""
        try:
            await vector_database_service.disconnect()
            await content_chunking_service.disconnect()
            logger.info("Disconnected from all services")
        except Exception as e:
            logger.error(f"Error disconnecting from services: {str(e)}")
    
    async def get_materials_needing_embeddings(self, limit: int = 100, modified_since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get materials that need embeddings generated or updated.
        
        Args:
            limit: Maximum number of materials to return
            modified_since: Only get materials modified since this datetime
            
        Returns:
            List of materials needing embeddings
        """
        try:
            # Build the where clause
            where = {}
            
            # Add modified_since filter if provided
            if modified_since:
                where["updatedAt"] = {"gt": modified_since}
            
            # Get materials
            materials = await prisma.material.find_many(
                where=where,
                take=limit,
                include={
                    "contentChunks": True
                }
            )
            
            # Filter materials that need embeddings
            materials_needing_embeddings = []
            for material in materials:
                # Check if material has no content chunks
                if not material.contentChunks:
                    materials_needing_embeddings.append(material)
                    continue
                
                # Check if any content chunks don't have embeddings
                chunks_without_embeddings = [chunk for chunk in material.contentChunks if not chunk.embedding]
                if chunks_without_embeddings:
                    materials_needing_embeddings.append(material)
                    continue
                
                # Check if material was updated after the last chunk was created
                if material.contentChunks and material.updatedAt:
                    newest_chunk = max(material.contentChunks, key=lambda x: x.createdAt if x.createdAt else datetime.min)
                    if newest_chunk.createdAt and material.updatedAt > newest_chunk.createdAt:
                        materials_needing_embeddings.append(material)
            
            return materials_needing_embeddings
        except Exception as e:
            logger.error(f"Error getting materials needing embeddings: {str(e)}")
            return []
    
    async def process_material(self, material_id: str) -> bool:
        """Process a single material for embeddings.
        
        Args:
            material_id: ID of the material to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            start_time = time.time()
            logger.info(f"Processing material {material_id} for embeddings")
            
            # Step 1: Chunk the material content
            chunks = await content_chunking_service.chunk_material(material_id)
            if not chunks:
                logger.warning(f"No chunks created for material {material_id}")
                return False
            
            # Step 2: Generate and store embeddings for each chunk
            chunks_data = [
                {
                    "id": chunk.id,
                    "content": chunk.content,
                    "material_id": chunk.materialId
                }
                for chunk in chunks
            ]
            
            # Process in batches to avoid rate limiting
            success = True
            for i in range(0, len(chunks_data), self.batch_size):
                batch = chunks_data[i:i+self.batch_size]
                batch_success = await vector_database_service.batch_generate_embeddings(batch)
                
                if not batch_success:
                    success = False
                    self.metrics["failed_embeddings"] += len(batch)
                else:
                    self.metrics["embeddings_generated"] += len(batch)
                    self.metrics["chunks_processed"] += len(batch)
                    # Estimate tokens (approximately 4 tokens per word)
                    for chunk in batch:
                        self.metrics["total_tokens"] += len(chunk["content"].split()) * 4
                
                # Add delay to avoid rate limiting
                if i + self.batch_size < len(chunks_data):
                    await asyncio.sleep(self.rate_limit_delay)
            
            # Update metrics
            if success:
                self.metrics["materials_processed"] += 1
            
            processing_time = time.time() - start_time
            self.metrics["total_processing_time"] += processing_time
            
            logger.info(f"Processed material {material_id} in {processing_time:.2f} seconds")
            return success
        except Exception as e:
            logger.error(f"Error processing material {material_id}: {str(e)}")
            return False
    
    async def process_materials_batch(self, material_ids: List[str]) -> Tuple[int, int]:
        """Process a batch of materials for embeddings.
        
        Args:
            material_ids: List of material IDs to process
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0
        
        for material_id in material_ids:
            success = await self.process_material(material_id)
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(self.rate_limit_delay)
        
        return success_count, failure_count
    
    async def run_embedding_pipeline(self, limit: int = 100, modified_since: Optional[datetime] = None) -> Dict[str, Any]:
        """Run the full embedding pipeline.
        
        Args:
            limit: Maximum number of materials to process
            modified_since: Only process materials modified since this datetime
            
        Returns:
            Dictionary with pipeline run results
        """
        try:
            start_time = time.time()
            logger.info(f"Starting embedding pipeline run")
            
            # Reset metrics for this run
            self.metrics["materials_processed"] = 0
            self.metrics["chunks_processed"] = 0
            self.metrics["embeddings_generated"] = 0
            self.metrics["failed_embeddings"] = 0
            self.metrics["total_tokens"] = 0
            self.metrics["total_processing_time"] = 0
            
            # Connect to services
            connected = await self.connect()
            if not connected:
                logger.error("Failed to connect to required services")
                return {"success": False, "error": "Failed to connect to required services"}
            
            # Get materials needing embeddings
            materials = await self.get_materials_needing_embeddings(limit, modified_since)
            if not materials:
                logger.info("No materials need embeddings")
                await self.disconnect()
                return {
                    "success": True,
                    "materials_processed": 0,
                    "message": "No materials need embeddings"
                }
            
            logger.info(f"Found {len(materials)} materials needing embeddings")
            
            # Process materials
            material_ids = [material.id for material in materials]
            success_count, failure_count = await self.process_materials_batch(material_ids)
            
            # Update last run timestamp
            self.metrics["last_run"] = datetime.now()
            
            # Disconnect from services
            await self.disconnect()
            
            total_time = time.time() - start_time
            
            # Prepare result
            result = {
                "success": True,
                "materials_processed": success_count,
                "materials_failed": failure_count,
                "chunks_processed": self.metrics["chunks_processed"],
                "embeddings_generated": self.metrics["embeddings_generated"],
                "failed_embeddings": self.metrics["failed_embeddings"],
                "total_tokens": self.metrics["total_tokens"],
                "total_time_seconds": total_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Embedding pipeline run completed in {total_time:.2f} seconds")
            return result
        except Exception as e:
            logger.error(f"Error running embedding pipeline: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def schedule_embedding_pipeline(self, interval_hours: int = 24) -> None:
        """Schedule the embedding pipeline to run at regular intervals.
        
        Args:
            interval_hours: Interval in hours between pipeline runs
        """
        try:
            logger.info(f"Scheduling embedding pipeline to run every {interval_hours} hours")
            
            while True:
                # Run the pipeline
                await self.run_embedding_pipeline()
                
                # Wait for the next interval
                logger.info(f"Waiting {interval_hours} hours until next pipeline run")
                await asyncio.sleep(interval_hours * 3600)
        except Exception as e:
            logger.error(f"Error in scheduled embedding pipeline: {str(e)}")
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about embeddings in the system.
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            # Connect to the database
            await vector_database_service.connect()
            
            # Get total materials count
            total_materials = await prisma.material.count()
            
            # Get total content chunks count
            total_chunks = await prisma.contentchunk.count()
            
            # Get count of chunks with embeddings
            chunks_with_embeddings = await prisma.execute_raw(
                "SELECT COUNT(*) FROM content_chunks WHERE embedding IS NOT NULL"
            )
            chunks_with_embeddings = chunks_with_embeddings[0][0] if chunks_with_embeddings else 0
            
            # Get count of chunks without embeddings
            chunks_without_embeddings = total_chunks - chunks_with_embeddings
            
            # Get count of materials with all chunks embedded
            materials_with_all_chunks_embedded = await prisma.execute_raw(
                """
                SELECT COUNT(DISTINCT m.id) 
                FROM materials m
                WHERE NOT EXISTS (
                    SELECT 1 FROM content_chunks c 
                    WHERE c.material_id = m.id AND c.embedding IS NULL
                )
                AND EXISTS (
                    SELECT 1 FROM content_chunks c 
                    WHERE c.material_id = m.id
                )
                """
            )
            materials_with_all_chunks_embedded = materials_with_all_chunks_embedded[0][0] if materials_with_all_chunks_embedded else 0
            
            # Get count of materials with some chunks embedded
            materials_with_some_chunks_embedded = await prisma.execute_raw(
                """
                SELECT COUNT(DISTINCT m.id) 
                FROM materials m
                WHERE EXISTS (
                    SELECT 1 FROM content_chunks c 
                    WHERE c.material_id = m.id AND c.embedding IS NOT NULL
                )
                AND EXISTS (
                    SELECT 1 FROM content_chunks c 
                    WHERE c.material_id = m.id AND c.embedding IS NULL
                )
                """
            )
            materials_with_some_chunks_embedded = materials_with_some_chunks_embedded[0][0] if materials_with_some_chunks_embedded else 0
            
            # Get count of materials with no chunks embedded
            materials_with_no_chunks_embedded = total_materials - materials_with_all_chunks_embedded - materials_with_some_chunks_embedded
            
            # Disconnect from the database
            await vector_database_service.disconnect()
            
            return {
                "total_materials": total_materials,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
                "chunks_without_embeddings": chunks_without_embeddings,
                "materials_with_all_chunks_embedded": materials_with_all_chunks_embedded,
                "materials_with_some_chunks_embedded": materials_with_some_chunks_embedded,
                "materials_with_no_chunks_embedded": materials_with_no_chunks_embedded,
                "embedding_coverage_percentage": (chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0,
                "material_coverage_percentage": (materials_with_all_chunks_embedded / total_materials * 100) if total_materials > 0 else 0,
                "last_pipeline_run": self.metrics["last_run"].isoformat() if self.metrics["last_run"] else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting embedding stats: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance of the EmbeddingPipelineService
embedding_pipeline_service = EmbeddingPipelineService()
