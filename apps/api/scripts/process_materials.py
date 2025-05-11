#!/usr/bin/env python3
"""
Script to process materials into content chunks and generate vector embeddings.

This script handles the full pipeline from chunking materials to generating and storing
vector embeddings for semantic search and AI-powered content retrieval.

Usage:
    python process_materials.py [material_id] [--chunks-only] [--embeddings-only] [--batch-size N] [--limit N]

Options:
    material_id         Process a specific material by ID
    --chunks-only       Only chunk materials, don't generate embeddings
    --embeddings-only   Only generate embeddings for existing chunks
    --batch-size N      Process materials in batches of N (default: 50)
    --limit N           Process at most N materials (default: 100)

Examples:
    # Process all materials (chunking and embeddings)
    python process_materials.py
    
    # Process a specific material
    python process_materials.py abc123
    
    # Only chunk materials, don't generate embeddings
    python process_materials.py --chunks-only
    
    # Only generate embeddings for existing chunks
    python process_materials.py --embeddings-only
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import services
from app.services.content_chunking import content_chunking_service
from app.services.vector_database import vector_database_service
from app.services.embedding_pipeline import embedding_pipeline_service

async def process_single_material(material_id, chunks_only=False, embeddings_only=False):
    """Process a single material into content chunks and generate embeddings.
    
    Args:
        material_id: ID of the material to process
        chunks_only: Only chunk the material, don't generate embeddings
        embeddings_only: Only generate embeddings for existing chunks
        
    Returns:
        True if successful, False otherwise
    """
    try:
        start_time = datetime.now()
        logger.info(f"Processing material {material_id}")
        
        # Step 1: Chunk the material (if not embeddings_only)
        chunks = []
        if not embeddings_only:
            # Connect to the database
            await content_chunking_service.connect()
            
            # Process the material
            chunks = await content_chunking_service.chunk_material(material_id)
            
            # Disconnect from the database
            await content_chunking_service.disconnect()
            
            if chunks:
                logger.info(f"Successfully chunked material {material_id} into {len(chunks)} chunks")
            else:
                logger.error(f"Failed to chunk material {material_id}")
                return False
        
        # Step 2: Generate embeddings (if not chunks_only)
        if not chunks_only:
            # Use the embedding pipeline service to process the material
            success = await embedding_pipeline_service.process_material(material_id)
            
            if success:
                logger.info(f"Successfully generated embeddings for material {material_id}")
            else:
                logger.error(f"Failed to generate embeddings for material {material_id}")
                return False
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Processed material {material_id} in {elapsed_time:.2f} seconds")
        return True
    except Exception as e:
        logger.error(f"Error processing material {material_id}: {str(e)}")
        return False

async def process_all_materials(chunks_only=False, embeddings_only=False, batch_size=50, limit=100):
    """Process all materials that need processing.
    
    Args:
        chunks_only: Only chunk materials, don't generate embeddings
        embeddings_only: Only generate embeddings for existing chunks
        batch_size: Number of materials to process in each batch
        limit: Maximum number of materials to process
        
    Returns:
        Number of materials successfully processed
    """
    try:
        start_time = datetime.now()
        logger.info(f"Processing all materials (limit: {limit}, batch_size: {batch_size})")
        
        # Step 1: Chunk materials (if not embeddings_only)
        if not embeddings_only:
            # Connect to the database
            await content_chunking_service.connect()
            
            # Process all materials
            processed_count = await content_chunking_service.process_all_materials()
            
            # Disconnect from the database
            await content_chunking_service.disconnect()
            
            logger.info(f"Chunked {processed_count} materials")
        
        # Step 2: Generate embeddings (if not chunks_only)
        if not chunks_only:
            # Use the embedding pipeline service to process materials
            result = await embedding_pipeline_service.run_embedding_pipeline(limit=limit)
            
            if result.get("success", False):
                logger.info(f"Generated embeddings for {result.get('materials_processed', 0)} materials")
                logger.info(f"Processed {result.get('chunks_processed', 0)} chunks")
                logger.info(f"Generated {result.get('embeddings_generated', 0)} embeddings")
                logger.info(f"Failed embeddings: {result.get('failed_embeddings', 0)}")
            else:
                logger.error(f"Failed to run embedding pipeline: {result.get('error', 'Unknown error')}")
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Processed all materials in {elapsed_time:.2f} seconds")
        
        # Get embedding stats
        stats = await embedding_pipeline_service.get_embedding_stats()
        logger.info(f"Embedding coverage: {stats.get('embedding_coverage_percentage', 0):.2f}%")
        logger.info(f"Material coverage: {stats.get('material_coverage_percentage', 0):.2f}%")
        
        return result.get('materials_processed', 0) if not chunks_only else processed_count
    except Exception as e:
        logger.error(f"Error processing all materials: {str(e)}")
        return 0

async def main():
    """Main function to run the script."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Process materials into content chunks and generate embeddings")
        parser.add_argument("material_id", nargs="?", help="Process a specific material by ID")
        parser.add_argument("--chunks-only", action="store_true", help="Only chunk materials, don't generate embeddings")
        parser.add_argument("--embeddings-only", action="store_true", help="Only generate embeddings for existing chunks")
        parser.add_argument("--batch-size", type=int, default=50, help="Process materials in batches of N (default: 50)")
        parser.add_argument("--limit", type=int, default=100, help="Process at most N materials (default: 100)")
        args = parser.parse_args()
        
        # Process a specific material or all materials
        if args.material_id:
            logger.info(f"Processing material {args.material_id}")
            success = await process_single_material(
                args.material_id,
                chunks_only=args.chunks_only,
                embeddings_only=args.embeddings_only
            )
            return 0 if success else 1
        else:
            logger.info("Processing all materials")
            processed_count = await process_all_materials(
                chunks_only=args.chunks_only,
                embeddings_only=args.embeddings_only,
                batch_size=args.batch_size,
                limit=args.limit
            )
            return 0 if processed_count > 0 else 1
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
