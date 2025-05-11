import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from prisma.models import Material, ContentChunk
from prisma.client import Prisma

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentChunkingService:
    """Service for chunking content into smaller pieces for vector embeddings."""
    
    def __init__(self):
        """Initialize the content chunking service."""
        self.prisma = Prisma()
        self.max_chunk_size = 1000  # Maximum characters per chunk
        self.overlap = 100  # Overlap between chunks to maintain context
    
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
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks of appropriate size for embedding.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # If text is shorter than max chunk size, return it as is
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Get a chunk of text
            end = start + self.max_chunk_size
            
            if end < len(text):
                # Try to find a natural break point (paragraph, sentence, etc.)
                break_point = self._find_break_point(text, start, end)
                chunk = text[start:break_point]
                start = break_point - self.overlap if break_point > self.overlap else break_point
            else:
                # Last chunk
                chunk = text[start:]
                start = len(text)
            
            chunks.append(chunk)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace, etc."""
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', text)
        
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find a natural break point in the text between start and end."""
        # Try to break at paragraph
        paragraph_break = text.rfind('\n', start, end)
        if paragraph_break != -1:
            return paragraph_break
        
        # Try to break at sentence
        sentence_break = text.rfind('. ', start, end)
        if sentence_break != -1:
            return sentence_break + 1  # Include the period
        
        # Try to break at other punctuation
        for punct in [';', ':', ',']:
            punct_break = text.rfind(punct, start, end)
            if punct_break != -1:
                return punct_break + 1  # Include the punctuation
        
        # If no natural break point, break at a word boundary
        space_break = text.rfind(' ', start, end)
        if space_break != -1:
            return space_break
        
        # If all else fails, break at the maximum length
        return end
    
    async def chunk_material(self, material_id: str) -> List[ContentChunk]:
        """Chunk a material's content and store in the database.
        
        Args:
            material_id: ID of the material to chunk
            
        Returns:
            List of created content chunks
        """
        try:
            # Get the material
            material = await self.prisma.material.find_unique(
                where={
                    'id': material_id
                }
            )
            
            if not material:
                logger.error(f"Material {material_id} not found")
                return []
            
            # Get existing content chunks for this material
            existing_chunks = await self.prisma.contentchunk.find_many(
                where={
                    'materialId': material_id
                }
            )
            
            # If chunks already exist, return them
            if existing_chunks:
                logger.info(f"Material {material_id} already has {len(existing_chunks)} chunks")
                return existing_chunks
            
            # For now, we'll just use the description as the content
            # In a real implementation, you would extract content from the file
            content = material.description
            
            # Chunk the content
            chunks = self.chunk_text(content)
            
            # Store chunks in the database
            created_chunks = []
            for chunk_text in chunks:
                chunk = await self.prisma.contentchunk.create(
                    data={
                        'content': chunk_text,
                        'materialId': material_id
                    }
                )
                created_chunks.append(chunk)
            
            logger.info(f"Created {len(created_chunks)} chunks for material {material_id}")
            return created_chunks
        except Exception as e:
            logger.error(f"Error chunking material: {str(e)}")
            return []
    
    async def process_all_materials(self) -> int:
        """Process all materials that don't have content chunks yet.
        
        Returns:
            Number of materials processed
        """
        try:
            # Get all materials
            materials = await self.prisma.material.find_many()
            
            processed_count = 0
            for material in materials:
                # Check if material already has chunks
                existing_chunks = await self.prisma.contentchunk.find_many(
                    where={
                        'materialId': material.id
                    }
                )
                
                if not existing_chunks:
                    # Chunk the material
                    chunks = await self.chunk_material(material.id)
                    if chunks:
                        processed_count += 1
            
            logger.info(f"Processed {processed_count} materials")
            return processed_count
        except Exception as e:
            logger.error(f"Error processing all materials: {str(e)}")
            return 0

# Create a singleton instance of the ContentChunkingService
content_chunking_service = ContentChunkingService()
