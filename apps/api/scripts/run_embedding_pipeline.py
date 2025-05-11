#!/usr/bin/env python3
"""
Script to run the embedding generation pipeline.

This script processes materials that need embeddings, either as a one-time job
or as a scheduled task that runs at regular intervals.

Usage:
    python run_embedding_pipeline.py [--limit N] [--schedule HOURS] [--modified-since DAYS] [--stats]

Options:
    --limit N            Maximum number of materials to process (default: 100)
    --schedule HOURS     Run the pipeline every HOURS hours (default: not scheduled)
    --modified-since DAYS Only process materials modified in the last DAYS days
    --stats              Show embedding statistics and exit

Examples:
    # Process up to 50 materials
    python run_embedding_pipeline.py --limit 50
    
    # Process materials modified in the last 7 days
    python run_embedding_pipeline.py --modified-since 7
    
    # Run the pipeline every 12 hours
    python run_embedding_pipeline.py --schedule 12
    
    # Show embedding statistics
    python run_embedding_pipeline.py --stats
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import services
from app.services.embedding_pipeline import embedding_pipeline_service

async def run_pipeline(args):
    """Run the embedding pipeline with the specified arguments."""
    # Parse modified_since if provided
    modified_since = None
    if args.modified_since:
        modified_since = datetime.now() - timedelta(days=args.modified_since)
        logger.info(f"Only processing materials modified since {modified_since}")
    
    # Run the pipeline
    result = await embedding_pipeline_service.run_embedding_pipeline(
        limit=args.limit,
        modified_since=modified_since
    )
    
    # Print results
    if result.get("success", False):
        logger.info(f"Pipeline run completed successfully")
        logger.info(f"Materials processed: {result.get('materials_processed', 0)}")
        logger.info(f"Chunks processed: {result.get('chunks_processed', 0)}")
        logger.info(f"Embeddings generated: {result.get('embeddings_generated', 0)}")
        logger.info(f"Failed embeddings: {result.get('failed_embeddings', 0)}")
        logger.info(f"Total tokens: {result.get('total_tokens', 0)}")
        logger.info(f"Total time: {result.get('total_time_seconds', 0):.2f} seconds")
    else:
        logger.error(f"Pipeline run failed: {result.get('error', 'Unknown error')}")
    
    return result

async def show_stats():
    """Show embedding statistics."""
    stats = await embedding_pipeline_service.get_embedding_stats()
    
    if "error" in stats:
        logger.error(f"Error getting stats: {stats['error']}")
        return
    
    logger.info("===== Embedding Statistics =====")
    logger.info(f"Total materials: {stats.get('total_materials', 0)}")
    logger.info(f"Total chunks: {stats.get('total_chunks', 0)}")
    logger.info(f"Chunks with embeddings: {stats.get('chunks_with_embeddings', 0)}")
    logger.info(f"Chunks without embeddings: {stats.get('chunks_without_embeddings', 0)}")
    logger.info(f"Materials with all chunks embedded: {stats.get('materials_with_all_chunks_embedded', 0)}")
    logger.info(f"Materials with some chunks embedded: {stats.get('materials_with_some_chunks_embedded', 0)}")
    logger.info(f"Materials with no chunks embedded: {stats.get('materials_with_no_chunks_embedded', 0)}")
    logger.info(f"Embedding coverage: {stats.get('embedding_coverage_percentage', 0):.2f}%")
    logger.info(f"Material coverage: {stats.get('material_coverage_percentage', 0):.2f}%")
    logger.info(f"Last pipeline run: {stats.get('last_pipeline_run', 'Never')}")

async def main():
    """Main function to run the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the embedding generation pipeline")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of materials to process")
    parser.add_argument("--schedule", type=int, help="Run the pipeline every HOURS hours")
    parser.add_argument("--modified-since", type=int, help="Only process materials modified in the last DAYS days")
    parser.add_argument("--stats", action="store_true", help="Show embedding statistics and exit")
    args = parser.parse_args()
    
    try:
        # Show stats if requested
        if args.stats:
            await show_stats()
            return 0
        
        # Run as a scheduled task if requested
        if args.schedule:
            logger.info(f"Starting scheduled embedding pipeline (every {args.schedule} hours)")
            await embedding_pipeline_service.schedule_embedding_pipeline(interval_hours=args.schedule)
        else:
            # Run once
            logger.info("Starting one-time embedding pipeline run")
            await run_pipeline(args)
        
        return 0
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
