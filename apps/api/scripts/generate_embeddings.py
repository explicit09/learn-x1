#!/usr/bin/env python3
"""
Script to generate embeddings for content chunks and store them in the database.
This script processes content chunks that don't have embeddings yet.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import services
from app.services.vector_database import vector_database_service
from app.services.openai import openai_service

async def ensure_vector_database_setup():
    """Ensure the vector database is properly set up."""
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
    
    logger.info("Vector database setup completed successfully")
    return True

async def process_content_chunks(batch_size=50, max_chunks=1000):
    """Process content chunks that don't have embeddings yet."""
    try:
        total_processed = 0
        
        while total_processed < max_chunks:
            # Get content chunks without embeddings
            content_chunks = await vector_database_service.get_content_chunks_without_embeddings(limit=batch_size)
            
            if not content_chunks:
                logger.info("No more content chunks without embeddings")
                break
            
            logger.info(f"Processing {len(content_chunks)} content chunks")
            
            # Generate and store embeddings in batch
            success = await vector_database_service.batch_generate_embeddings(content_chunks)
            
            if success:
                total_processed += len(content_chunks)
                logger.info(f"Successfully processed {total_processed} content chunks so far")
            else:
                logger.error(f"Failed to process batch of content chunks")
                break
            
            # Sleep briefly to avoid rate limiting
            await asyncio.sleep(1)
        
        logger.info(f"Completed processing {total_processed} content chunks")
        return total_processed
    except Exception as e:
        logger.error(f"Error processing content chunks: {str(e)}")
        return 0

async def process_material(material_id):
    """Process a specific material for embeddings."""
    try:
        logger.info(f"Processing material {material_id} for embeddings")
        
        success = await vector_database_service.process_material_for_embeddings(material_id)
        
        if success:
            logger.info(f"Successfully processed material {material_id}")
        else:
            logger.error(f"Failed to process material {material_id}")
        
        return success
    except Exception as e:
        logger.error(f"Error processing material: {str(e)}")
        return False

async def test_similarity_search(query):
    """Test similarity search with a query."""
    try:
        logger.info(f"Testing similarity search with query: '{query}'")
        
        results = await vector_database_service.similarity_search(query)
        
        if results:
            logger.info(f"Found {len(results)} similar content chunks")
            for i, result in enumerate(results[:5]):  # Show top 5 results
                logger.info(f"Result {i+1}: Similarity {result['similarity']:.4f}")
                logger.info(f"Content: {result['content'][:100]}...")
        else:
            logger.info("No similar content found")
        
        return results
    except Exception as e:
        logger.error(f"Error testing similarity search: {str(e)}")
        return []

async def main():
    """Main function to run the script."""
    try:
        # Ensure vector database is set up
        setup_success = await ensure_vector_database_setup()
        if not setup_success:
            logger.error("Failed to set up vector database")
            return 1
        
        # Process command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "process":
                # Process content chunks without embeddings
                batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
                max_chunks = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
                
                processed = await process_content_chunks(batch_size, max_chunks)
                logger.info(f"Processed {processed} content chunks")
            
            elif command == "material":
                # Process a specific material
                if len(sys.argv) < 3:
                    logger.error("Material ID is required")
                    return 1
                
                material_id = sys.argv[2]
                success = await process_material(material_id)
                
                if not success:
                    return 1
            
            elif command == "search":
                # Test similarity search
                if len(sys.argv) < 3:
                    logger.error("Search query is required")
                    return 1
                
                query = sys.argv[2]
                await test_similarity_search(query)
            
            else:
                logger.error(f"Unknown command: {command}")
                logger.info("Available commands: process, material, search")
                return 1
        else:
            # Default: process content chunks
            processed = await process_content_chunks()
            logger.info(f"Processed {processed} content chunks")
        
        # Disconnect from the database
        await vector_database_service.disconnect()
        
        return 0
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
