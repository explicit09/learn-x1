#!/usr/bin/env python3
"""
Script to apply the vector migration to the database.
This sets up pgvector extension and creates the necessary tables and functions.
"""

import os
import sys
import asyncio
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

# Path to migration file
MIGRATION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "prisma", "migrations", "20250509_add_vector_embeddings", "migration.sql"
)

async def apply_migration():
    """Apply the vector migration to the database."""
    try:
        # Read migration SQL
        with open(MIGRATION_FILE, "r") as f:
            migration_sql = f.read()
        
        # Connect to the database
        logger.info(f"Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Execute migration SQL
        logger.info(f"Applying vector migration...")
        cursor.execute(migration_sql)
        
        # Close connection
        cursor.close()
        conn.close()
        
        logger.info("Vector migration applied successfully")
        return True
    except Exception as e:
        logger.error(f"Error applying vector migration: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(apply_migration())
    sys.exit(0 if result else 1)
