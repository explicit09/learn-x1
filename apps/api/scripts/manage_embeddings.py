#!/usr/bin/env python3
"""
Script for monitoring and managing embeddings in the LEARN-X platform.

This script provides utilities for monitoring embedding status, reprocessing
embeddings, and cleaning up problematic embeddings.

Usage:
    python manage_embeddings.py [command] [options]

Commands:
    status          Show embedding status and statistics
    reprocess       Reprocess embeddings for specific materials or all materials
    cleanup         Clean up problematic embeddings
    monitor         Start a monitoring dashboard for embeddings

Options:
    --material-id ID   Specify a material ID for reprocessing
    --organization-id ID Specify an organization ID for filtering
    --force            Force reprocessing even for materials with embeddings
    --days DAYS        Only consider materials modified in the last DAYS days
    --limit N          Limit the number of materials to process

Examples:
    # Show embedding status
    python manage_embeddings.py status
    
    # Reprocess embeddings for a specific material
    python manage_embeddings.py reprocess --material-id abc123
    
    # Reprocess all materials for an organization
    python manage_embeddings.py reprocess --organization-id org123
    
    # Clean up problematic embeddings
    python manage_embeddings.py cleanup
    
    # Start monitoring dashboard
    python manage_embeddings.py monitor
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
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
from app.services.vector_database import vector_database_service
from app.services.prisma import prisma

async def show_status():
    """Show embedding status and statistics."""
    # Get embedding stats
    stats = await embedding_pipeline_service.get_embedding_stats()
    
    if "error" in stats:
        logger.error(f"Error getting stats: {stats['error']}")
        return False
    
    # Print stats in a formatted way
    print("\n===== LEARN-X Embedding Status =====\n")
    print(f"Total materials: {stats.get('total_materials', 0)}")
    print(f"Total content chunks: {stats.get('total_chunks', 0)}")
    print(f"\nEmbedding Coverage:")
    print(f"  Chunks with embeddings: {stats.get('chunks_with_embeddings', 0)} ({stats.get('embedding_coverage_percentage', 0):.2f}%)")
    print(f"  Chunks without embeddings: {stats.get('chunks_without_embeddings', 0)}")
    print(f"\nMaterial Coverage:")
    print(f"  Materials fully embedded: {stats.get('materials_with_all_chunks_embedded', 0)} ({stats.get('material_coverage_percentage', 0):.2f}%)")
    print(f"  Materials partially embedded: {stats.get('materials_with_some_chunks_embedded', 0)}")
    print(f"  Materials not embedded: {stats.get('materials_with_no_chunks_embedded', 0)}")
    print(f"\nLast pipeline run: {stats.get('last_pipeline_run', 'Never')}")
    print(f"Current timestamp: {stats.get('timestamp', datetime.now().isoformat())}")
    
    return True

async def reprocess_embeddings(material_id: Optional[str] = None, organization_id: Optional[str] = None, 
                              force: bool = False, days: Optional[int] = None, limit: int = 100):
    """Reprocess embeddings for materials.
    
    Args:
        material_id: Specific material ID to reprocess
        organization_id: Organization ID to filter materials
        force: Force reprocessing even for materials with embeddings
        days: Only consider materials modified in the last N days
        limit: Maximum number of materials to process
    """
    try:
        # Connect to the database
        await vector_database_service.connect()
        
        # Build the where clause
        where = {}
        
        # Add material_id filter if provided
        if material_id:
            where["id"] = material_id
        
        # Add organization_id filter if provided
        if organization_id:
            where["organizationId"] = organization_id
        
        # Add modified_since filter if provided
        if days:
            modified_since = datetime.now() - timedelta(days=days)
            where["updatedAt"] = {"gt": modified_since}
        
        # Get materials
        materials = await prisma.material.find_many(
            where=where,
            take=limit,
            include={
                "contentChunks": True,
                "organization": True
            }
        )
        
        if not materials:
            logger.info("No materials found matching the criteria")
            return False
        
        logger.info(f"Found {len(materials)} materials matching the criteria")
        
        # Filter materials based on force flag
        if not force:
            # Only process materials that need embeddings
            materials_to_process = []
            for material in materials:
                # Check if material has no content chunks
                if not material.contentChunks:
                    materials_to_process.append(material)
                    continue
                
                # Check if any content chunks don't have embeddings
                chunks_without_embeddings = [chunk for chunk in material.contentChunks if not chunk.embedding]
                if chunks_without_embeddings:
                    materials_to_process.append(material)
                    continue
            
            materials = materials_to_process
        
        if not materials:
            logger.info("No materials need reprocessing")
            return False
        
        logger.info(f"Reprocessing embeddings for {len(materials)} materials")
        
        # Process each material
        success_count = 0
        for material in materials:
            # First, delete existing chunks if any
            if material.contentChunks:
                await prisma.contentchunk.delete_many(
                    where={"materialId": material.id}
                )
                logger.info(f"Deleted existing chunks for material {material.id}")
            
            # Process the material
            success = await embedding_pipeline_service.process_material(material.id)
            if success:
                success_count += 1
                logger.info(f"Successfully reprocessed material {material.id}")
            else:
                logger.error(f"Failed to reprocess material {material.id}")
        
        logger.info(f"Reprocessing completed. Success: {success_count}, Failed: {len(materials) - success_count}")
        
        # Disconnect from the database
        await vector_database_service.disconnect()
        
        return success_count > 0
    except Exception as e:
        logger.error(f"Error reprocessing embeddings: {str(e)}")
        return False

async def cleanup_embeddings():
    """Clean up problematic embeddings."""
    try:
        # Connect to the database
        await vector_database_service.connect()
        
        # 1. Find content chunks with NULL embeddings
        null_embedding_count = await prisma.execute_raw(
            "SELECT COUNT(*) FROM content_chunks WHERE embedding IS NULL"
        )
        null_embedding_count = null_embedding_count[0][0] if null_embedding_count else 0
        
        # 2. Find content chunks with invalid embeddings (wrong dimension)
        invalid_embedding_count = await prisma.execute_raw(
            f"SELECT COUNT(*) FROM content_chunks WHERE embedding IS NOT NULL AND array_length(embedding, 1) != {embedding_pipeline_service.embedding_dimension}"
        )
        invalid_embedding_count = invalid_embedding_count[0][0] if invalid_embedding_count else 0
        
        # 3. Find orphaned content chunks (no associated material)
        orphaned_chunk_count = await prisma.execute_raw(
            """SELECT COUNT(*) FROM content_chunks c 
            WHERE NOT EXISTS (SELECT 1 FROM materials m WHERE m.id = c.material_id)"""
        )
        orphaned_chunk_count = orphaned_chunk_count[0][0] if orphaned_chunk_count else 0
        
        # Print cleanup summary
        print("\n===== Embedding Cleanup Summary =====\n")
        print(f"Content chunks with NULL embeddings: {null_embedding_count}")
        print(f"Content chunks with invalid embeddings: {invalid_embedding_count}")
        print(f"Orphaned content chunks: {orphaned_chunk_count}")
        print(f"\nTotal problematic chunks: {null_embedding_count + invalid_embedding_count + orphaned_chunk_count}")
        
        # Ask for confirmation before cleanup
        if null_embedding_count + invalid_embedding_count + orphaned_chunk_count > 0:
            print("\nCleanup actions to be performed:")
            if null_embedding_count > 0:
                print(f"- Generate embeddings for {null_embedding_count} chunks with NULL embeddings")
            if invalid_embedding_count > 0:
                print(f"- Regenerate {invalid_embedding_count} invalid embeddings")
            if orphaned_chunk_count > 0:
                print(f"- Delete {orphaned_chunk_count} orphaned chunks")
            
            confirm = input("\nProceed with cleanup? (y/n): ")
            if confirm.lower() != 'y':
                print("Cleanup cancelled")
                await vector_database_service.disconnect()
                return False
            
            # Perform cleanup actions
            print("\nPerforming cleanup...")
            
            # 1. Process chunks with NULL embeddings
            if null_embedding_count > 0:
                null_chunks = await prisma.execute_raw(
                    "SELECT id, content, material_id FROM content_chunks WHERE embedding IS NULL LIMIT 1000"
                )
                
                chunks_data = [
                    {
                        "id": row[0],
                        "content": row[1],
                        "material_id": row[2]
                    }
                    for row in null_chunks
                ]
                
                # Process in batches
                batch_size = 50
                for i in range(0, len(chunks_data), batch_size):
                    batch = chunks_data[i:i+batch_size]
                    success = await vector_database_service.batch_generate_embeddings(batch)
                    print(f"Processed batch {i//batch_size + 1}/{(len(chunks_data) + batch_size - 1)//batch_size}: {'Success' if success else 'Failed'}")
                    await asyncio.sleep(1)  # Avoid rate limiting
            
            # 2. Process chunks with invalid embeddings
            if invalid_embedding_count > 0:
                invalid_chunks = await prisma.execute_raw(
                    f"SELECT id, content, material_id FROM content_chunks WHERE embedding IS NOT NULL AND array_length(embedding, 1) != {embedding_pipeline_service.embedding_dimension} LIMIT 1000"
                )
                
                chunks_data = [
                    {
                        "id": row[0],
                        "content": row[1],
                        "material_id": row[2]
                    }
                    for row in invalid_chunks
                ]
                
                # Process in batches
                batch_size = 50
                for i in range(0, len(chunks_data), batch_size):
                    batch = chunks_data[i:i+batch_size]
                    success = await vector_database_service.batch_generate_embeddings(batch)
                    print(f"Processed batch {i//batch_size + 1}/{(len(chunks_data) + batch_size - 1)//batch_size}: {'Success' if success else 'Failed'}")
                    await asyncio.sleep(1)  # Avoid rate limiting
            
            # 3. Delete orphaned chunks
            if orphaned_chunk_count > 0:
                deleted = await prisma.execute_raw(
                    """DELETE FROM content_chunks 
                    WHERE NOT EXISTS (SELECT 1 FROM materials m WHERE m.id = content_chunks.material_id)"""
                )
                print(f"Deleted {deleted} orphaned chunks")
            
            print("\nCleanup completed successfully")
        else:
            print("\nNo problematic chunks found. No cleanup needed.")
        
        # Disconnect from the database
        await vector_database_service.disconnect()
        
        return True
    except Exception as e:
        logger.error(f"Error cleaning up embeddings: {str(e)}")
        return False

async def monitor_embeddings():
    """Start a monitoring dashboard for embeddings."""
    try:
        print("\n===== LEARN-X Embedding Monitoring Dashboard =====\n")
        print("Press Ctrl+C to exit\n")
        
        # Monitor in a loop
        while True:
            # Clear screen (works on both Windows and Unix-like systems)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"===== LEARN-X Embedding Monitoring Dashboard =====  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Get embedding stats
            stats = await embedding_pipeline_service.get_embedding_stats()
            
            if "error" in stats:
                print(f"Error getting stats: {stats['error']}")
            else:
                # Print stats
                print(f"Total materials: {stats.get('total_materials', 0)}")
                print(f"Total content chunks: {stats.get('total_chunks', 0)}")
                print(f"\nEmbedding Coverage:")
                print(f"  Chunks with embeddings: {stats.get('chunks_with_embeddings', 0)} ({stats.get('embedding_coverage_percentage', 0):.2f}%)")
                print(f"  Chunks without embeddings: {stats.get('chunks_without_embeddings', 0)}")
                print(f"\nMaterial Coverage:")
                print(f"  Materials fully embedded: {stats.get('materials_with_all_chunks_embedded', 0)} ({stats.get('material_coverage_percentage', 0):.2f}%)")
                print(f"  Materials partially embedded: {stats.get('materials_with_some_chunks_embedded', 0)}")
                print(f"  Materials not embedded: {stats.get('materials_with_no_chunks_embedded', 0)}")
                print(f"\nLast pipeline run: {stats.get('last_pipeline_run', 'Never')}")
            
            # Get recent pipeline runs
            print("\nRecent Pipeline Runs:")
            # This would be implemented with a proper logging/history system
            # For now, just show a placeholder
            print("  No recent pipeline runs recorded")
            
            print("\nPress Ctrl+C to exit")
            
            # Wait before refreshing
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
        return True
    except Exception as e:
        logger.error(f"Error monitoring embeddings: {str(e)}")
        return False

async def main():
    """Main function to run the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Manage embeddings in the LEARN-X platform")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show embedding status and statistics")
    
    # Reprocess command
    reprocess_parser = subparsers.add_parser("reprocess", help="Reprocess embeddings for materials")
    reprocess_parser.add_argument("--material-id", help="Specific material ID to reprocess")
    reprocess_parser.add_argument("--organization-id", help="Organization ID to filter materials")
    reprocess_parser.add_argument("--force", action="store_true", help="Force reprocessing even for materials with embeddings")
    reprocess_parser.add_argument("--days", type=int, help="Only consider materials modified in the last N days")
    reprocess_parser.add_argument("--limit", type=int, default=100, help="Maximum number of materials to process")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up problematic embeddings")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start a monitoring dashboard for embeddings")
    
    args = parser.parse_args()
    
    # Execute the appropriate command
    try:
        if args.command == "status":
            await show_status()
        elif args.command == "reprocess":
            await reprocess_embeddings(
                material_id=args.material_id,
                organization_id=args.organization_id,
                force=args.force,
                days=args.days,
                limit=args.limit
            )
        elif args.command == "cleanup":
            await cleanup_embeddings()
        elif args.command == "monitor":
            await monitor_embeddings()
        else:
            parser.print_help()
        
        return 0
    except KeyboardInterrupt:
        logger.info("Command interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
