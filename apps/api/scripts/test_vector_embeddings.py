#!/usr/bin/env python3
"""
Script to test vector embeddings functionality.
This script creates test content, generates embeddings, and performs a similarity search.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
import numpy as np
from openai import OpenAI
import psycopg2
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable not set")
    sys.exit(1)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Test content
TEST_CONTENT = [
    "Machine learning is a field of study that gives computers the ability to learn without being explicitly programmed.",
    "Deep learning is part of a broader family of machine learning methods based on artificial neural networks.",
    "Natural language processing is a subfield of linguistics, computer science, and artificial intelligence.",
    "Computer vision is an interdisciplinary field that deals with how computers can gain high-level understanding from digital images or videos.",
    "Reinforcement learning is an area of machine learning concerned with how intelligent agents ought to take actions in an environment."
]

async def generate_embedding(text):
    """Generate embedding for a text using OpenAI API."""
    try:
        response = openai_client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None

async def create_test_material():
    """Create a test material in the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create a test topic
        topic_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO topics (id, title, description, order, module_id, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id",
            (topic_id, "Test Topic", "Test Topic Description", 1, "00000000-0000-0000-0000-000000000001")
        )
        
        # Create a test material
        material_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO materials (id, title, description, file_url, file_type, topic_id, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id",
            (material_id, "Test Material", "Test Material Description", "https://example.com/test.pdf", "PDF", topic_id)
        )
        
        # Create content chunks with embeddings
        chunk_ids = []
        for content in TEST_CONTENT:
            chunk_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO content_chunks (id, content, material_id, created_at, updated_at) "
                "VALUES (%s, %s, %s, NOW(), NOW()) RETURNING id",
                (chunk_id, content, material_id)
            )
            chunk_ids.append(chunk_id)
            
            # Generate and store embedding
            embedding = await generate_embedding(content)
            if embedding:
                embedding_str = '{' + ','.join(str(x) for x in embedding) + '}'
                cursor.execute(
                    "UPDATE content_chunks SET embedding = %s::vector WHERE id = %s",
                    (embedding_str, chunk_id)
                )
        
        cursor.close()
        conn.close()
        
        return material_id, chunk_ids
    except Exception as e:
        logger.error(f"Error creating test material: {str(e)}")
        return None, []

async def test_similarity_search(query):
    """Test similarity search with a query."""
    try:
        # Generate embedding for query
        query_embedding = await generate_embedding(query)
        if not query_embedding:
            return []
        
        query_embedding_str = '{' + ','.join(str(x) for x in query_embedding) + '}'
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Perform similarity search
        cursor.execute(
            """SELECT c.id, c.content, c.material_id, 
               1 - (c.embedding <=> %s::vector) as similarity
               FROM content_chunks c
               WHERE c.embedding IS NOT NULL
               ORDER BY c.embedding <=> %s::vector LIMIT 3
            """,
            (query_embedding_str, query_embedding_str)
        )
        
        results = cursor.fetchall()
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                "id": row[0],
                "content": row[1],
                "material_id": row[2],
                "similarity": float(row[3])
            })
        
        cursor.close()
        conn.close()
        
        return formatted_results
    except Exception as e:
        logger.error(f"Error performing similarity search: {str(e)}")
        return []

async def run_test():
    """Run the vector embeddings test."""
    logger.info("Starting vector embeddings test...")
    
    # Create test material and content chunks
    logger.info("Creating test material and content chunks...")
    material_id, chunk_ids = await create_test_material()
    if not material_id:
        logger.error("Failed to create test material")
        return False
    
    logger.info(f"Created material with ID: {material_id}")
    logger.info(f"Created {len(chunk_ids)} content chunks")
    
    # Test similarity search
    logger.info("Testing similarity search...")
    test_queries = [
        "How do computers learn?",
        "What is computer vision?",
        "Tell me about reinforcement learning"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        results = await test_similarity_search(query)
        
        if results:
            logger.info(f"Found {len(results)} similar content chunks:")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}:")
                logger.info(f"  Content: {result['content']}")
                logger.info(f"  Similarity: {result['similarity']:.4f}")
        else:
            logger.info("No similar content found")
    
    logger.info("\nVector embeddings test completed successfully")
    return True

if __name__ == "__main__":
    result = asyncio.run(run_test())
    sys.exit(0 if result else 1)
