import re
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextChunkingService:
    """Service for chunking text content for embedding generation."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the text chunking service.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks of specified size.
        
        Args:
            text: The text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # If text is shorter than chunk size, return it as a single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the end of the current chunk
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to find a natural break point (paragraph, sentence, or word boundary)
            chunk_end = self._find_break_point(text, end)
            
            # Add the chunk
            chunks.append(text[start:chunk_end])
            
            # Move the start position for the next chunk, accounting for overlap
            start = chunk_end - self.chunk_overlap
            
            # Ensure we're not stuck in a loop
            if start >= len(text) - 1:
                break
        
        return chunks
    
    def chunk_markdown(self, markdown: str) -> List[str]:
        """Split markdown text into chunks based on headers and sections.
        
        Args:
            markdown: The markdown text to split into chunks
            
        Returns:
            List of markdown chunks
        """
        if not markdown:
            return []
        
        # Split by headers
        header_pattern = r'^#{1,6}\s+.+$'
        lines = markdown.split('\n')
        sections = []
        current_section = []
        
        for line in lines:
            if re.match(header_pattern, line) and current_section:
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Further chunk each section if it's too large
        chunks = []
        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section)
            else:
                chunks.extend(self.chunk_text(section))
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and normalizing line breaks."""
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace multiple spaces with a single space
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()
    
    def _find_break_point(self, text: str, position: int) -> int:
        """Find a natural break point near the specified position.
        
        Tries to find a paragraph break, then a sentence break, then a word break.
        
        Args:
            text: The text to search in
            position: The approximate position to find a break
            
        Returns:
            The position of the natural break point
        """
        # Look for paragraph break
        paragraph_break = text.rfind('\n\n', position - self.chunk_size, position + 100)
        if paragraph_break != -1 and paragraph_break <= position + 100:
            return paragraph_break + 2
        
        # Look for single newline
        newline_break = text.rfind('\n', position - self.chunk_size, position + 50)
        if newline_break != -1 and newline_break <= position + 50:
            return newline_break + 1
        
        # Look for sentence break
        sentence_break = -1
        for pattern in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
            temp_break = text.rfind(pattern, position - self.chunk_size, position + 20)
            if temp_break > sentence_break:
                sentence_break = temp_break
        
        if sentence_break != -1 and sentence_break <= position + 20:
            return sentence_break + 2
        
        # Look for word break
        word_break = text.rfind(' ', position - 50, position)
        if word_break != -1:
            return word_break + 1
        
        # If no natural break point is found, just break at the position
        return position

# Create a singleton instance of the TextChunkingService
text_chunking_service = TextChunkingService()
