#!/usr/bin/env python3
"""
Script to test the embedding pipeline functionality.

This script runs a series of tests on the embedding pipeline to ensure
all components are working correctly. It tests content chunking,
embedding generation, and vector search functionality.

Usage:
    python test_embedding_pipeline.py [--verbose] [--quick]

Options:
    --verbose       Show detailed output for each test
    --quick         Run a quick test with minimal API calls
"""

import os
import sys
import asyncio
import argparse
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
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
from app.services.openai import openai_service
from app.services.prisma import prisma

class EmbeddingPipelineTest:
    """Test class for the embedding pipeline."""
    
    def __init__(self, verbose=False, quick=False):
        self.verbose = verbose
        self.quick = quick
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    async def setup(self):
        """Set up the test environment."""
        # Connect to services
        await vector_database_service.connect()
        await embedding_pipeline_service.connect()
        
        # Ensure pgvector extension is enabled
        await vector_database_service.ensure_vector_extension()
        
        # Create a test material if needed for quick test
        if self.quick:
            # Check if test material exists
            test_material = await prisma.material.find_first(
                where={"title": {"contains": "Embedding Pipeline Test Material"}}
            )
            
            if not test_material:
                # Create a test organization if needed
                test_org = await prisma.organization.find_first()
                if not test_org:
                    test_org = await prisma.organization.create(
                        data={
                            "name": "Test Organization",
                            "slug": "test-org"
                        }
                    )
                
                # Create a test material
                test_material = await prisma.material.create(
                    data={
                        "title": "Embedding Pipeline Test Material",
                        "content": """# Embedding Pipeline Test
                        
                        This is a test material for the embedding pipeline. It contains multiple paragraphs
                        to ensure proper chunking and embedding generation.
                        
                        ## Section 1: Introduction
                        
                        The embedding pipeline is responsible for processing educational materials,
                        chunking them into smaller pieces, and generating vector embeddings for each chunk.
                        These embeddings are then used for semantic search and AI-powered content retrieval.
                        
                        ## Section 2: Implementation
                        
                        The pipeline consists of several components:
                        
                        1. Content Chunking Service: Breaks down materials into manageable chunks
                        2. OpenAI Service: Generates embeddings using the OpenAI API
                        3. Vector Database Service: Stores and retrieves embeddings
                        4. Embedding Pipeline Service: Orchestrates the entire process
                        
                        ## Section 3: Testing
                        
                        This material is used to test the embedding pipeline functionality.
                        It ensures that all components are working correctly and that the pipeline
                        can process materials, generate embeddings, and perform similarity searches.
                        """,
                        "organizationId": test_org.id,
                        "type": "DOCUMENT",
                        "status": "PUBLISHED"
                    }
                )
            
            self.test_material_id = test_material.id
            logger.info(f"Using test material: {self.test_material_id}")
    
    async def teardown(self):
        """Clean up after tests."""
        # Disconnect from services
        await vector_database_service.disconnect()
        await embedding_pipeline_service.disconnect()
    
    async def run_tests(self):
        """Run all tests."""
        self.start_time = datetime.now()
        
        # Run tests
        await self.test_content_chunking()
        await self.test_embedding_generation()
        await self.test_vector_search()
        await self.test_pipeline_execution()
        
        self.end_time = datetime.now()
        
        # Print summary
        self.print_summary()
    
    async def test_content_chunking(self):
        """Test content chunking functionality."""
        test_name = "Content Chunking"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test chunking a sample text
            sample_text = """
            # Sample Document
            
            This is a sample document with multiple paragraphs.
            It is used to test the content chunking functionality.
            
            ## Section 1
            
            The content chunking service breaks down documents into smaller chunks.
            These chunks are then processed by the embedding pipeline.
            
            ## Section 2
            
            Each chunk should be a meaningful unit of text.
            The chunks should preserve context and be suitable for embedding generation.
            """
            
            # Test chunk_text method
            chunks = content_chunking_service.chunk_text(sample_text)
            
            if self.verbose:
                logger.info(f"Generated {len(chunks)} chunks from sample text")
                for i, chunk in enumerate(chunks):
                    logger.info(f"Chunk {i+1}: {chunk[:50]}...")
            
            # Test with a real material if not in quick mode
            if not self.quick:
                # Get a random material
                material = await prisma.material.find_first(
                    where={
                        "contentChunks": {
                            "none": {}
                        }
                    }
                )
                
                if material:
                    await content_chunking_service.connect()
                    chunks = await content_chunking_service.chunk_material(material.id)
                    await content_chunking_service.disconnect()
                    
                    if self.verbose:
                        logger.info(f"Chunked material {material.id} into {len(chunks)} chunks")
                else:
                    # Use test material
                    await content_chunking_service.connect()
                    chunks = await content_chunking_service.chunk_material(self.test_material_id)
                    await content_chunking_service.disconnect()
                    
                    if self.verbose:
                        logger.info(f"Chunked test material into {len(chunks)} chunks")
            
            self.test_results.append({
                "name": test_name,
                "success": True,
                "message": f"Successfully chunked content into {len(chunks)} chunks"
            })
        except Exception as e:
            logger.error(f"Error in {test_name} test: {str(e)}")
            self.test_results.append({
                "name": test_name,
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    async def test_embedding_generation(self):
        """Test embedding generation functionality."""
        test_name = "Embedding Generation"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test generating embeddings for a sample text
            sample_text = "This is a sample text for embedding generation."
            
            # Generate embedding
            embedding = await openai_service.create_embedding(sample_text)
            
            if self.verbose:
                logger.info(f"Generated embedding with {len(embedding)} dimensions")
            
            # Verify embedding dimension
            expected_dimension = embedding_pipeline_service.embedding_dimension
            assert len(embedding) == expected_dimension, f"Embedding dimension mismatch: expected {expected_dimension}, got {len(embedding)}"
            
            self.test_results.append({
                "name": test_name,
                "success": True,
                "message": f"Successfully generated embedding with {len(embedding)} dimensions"
            })
        except Exception as e:
            logger.error(f"Error in {test_name} test: {str(e)}")
            self.test_results.append({
                "name": test_name,
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    async def test_vector_search(self):
        """Test vector search functionality."""
        test_name = "Vector Search"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Skip if in quick mode and no embeddings exist
            if self.quick:
                # Check if we have any embeddings
                count = await prisma.contentchunk.count(
                    where={
                        "embedding": {
                            "not": None
                        }
                    }
                )
                
                if count == 0:
                    logger.info("No embeddings found, skipping vector search test")
                    self.test_results.append({
                        "name": test_name,
                        "success": True,
                        "message": "Skipped (no embeddings found)"
                    })
                    return
            
            # Test similarity search
            query = "embedding pipeline implementation"
            results = await vector_database_service.similarity_search(query, match_count=5)
            
            if self.verbose:
                logger.info(f"Found {len(results)} results for query: '{query}'")
                for i, result in enumerate(results):
                    logger.info(f"Result {i+1}: {result['content'][:50]}... (similarity: {result['similarity']:.4f})")
            
            self.test_results.append({
                "name": test_name,
                "success": True,
                "message": f"Successfully performed similarity search with {len(results)} results"
            })
        except Exception as e:
            logger.error(f"Error in {test_name} test: {str(e)}")
            self.test_results.append({
                "name": test_name,
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    async def test_pipeline_execution(self):
        """Test the full pipeline execution."""
        test_name = "Pipeline Execution"
        logger.info(f"Running test: {test_name}")
        
        try:
            if self.quick:
                # Process only the test material
                success = await embedding_pipeline_service.process_material(self.test_material_id)
                
                if self.verbose:
                    logger.info(f"Processed test material: {'Success' if success else 'Failed'}")
                
                self.test_results.append({
                    "name": test_name,
                    "success": success,
                    "message": f"{'Successfully' if success else 'Failed to'} process test material"
                })
            else:
                # Run the pipeline with a small limit
                result = await embedding_pipeline_service.run_embedding_pipeline(limit=5)
                
                if self.verbose:
                    logger.info(f"Pipeline execution result: {result}")
                
                success = result.get("success", False)
                self.test_results.append({
                    "name": test_name,
                    "success": success,
                    "message": f"{'Successfully' if success else 'Failed to'} run embedding pipeline"
                })
        except Exception as e:
            logger.error(f"Error in {test_name} test: {str(e)}")
            self.test_results.append({
                "name": test_name,
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    def print_summary(self):
        """Print a summary of the test results."""
        print("\n" + "=" * 50)
        print("EMBEDDING PIPELINE TEST RESULTS")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests / total_tests) * 100:.2f}%")
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"Duration: {duration:.2f} seconds")
        
        print("\nDetailed Results:")
        for i, result in enumerate(self.test_results):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{i+1}. {result['name']}: {status}")
            print(f"   {result['message']}")
        
        print("\n" + "=" * 50)

async def main():
    """Main function to run the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the embedding pipeline functionality")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output for each test")
    parser.add_argument("--quick", action="store_true", help="Run a quick test with minimal API calls")
    args = parser.parse_args()
    
    try:
        # Create and run the test suite
        test_suite = EmbeddingPipelineTest(verbose=args.verbose, quick=args.quick)
        
        # Setup
        await test_suite.setup()
        
        # Run tests
        await test_suite.run_tests()
        
        # Teardown
        await test_suite.teardown()
        
        # Determine exit code based on test results
        failed_tests = sum(1 for result in test_suite.test_results if not result["success"])
        return 1 if failed_tests > 0 else 0
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
