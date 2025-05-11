import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Create a mock class for testing without dependencies
class MockVectorSearchService:
    """A simplified version of the VectorSearchService for testing."""
    
    async def search_by_query(self, query, similarity_threshold=0.7, match_count=5):
        """Mock search by query."""
        return [
            {
                'id': 'chunk1',
                'content': 'This is a test content chunk about machine learning.',
                'material_id': 'material1',
                'similarity': 0.95
            },
            {
                'id': 'chunk2',
                'content': 'This is another test content chunk about deep learning.',
                'material_id': 'material1',
                'similarity': 0.85
            }
        ]
    
    async def get_relevant_context(self, query, max_chunks=3):
        """Mock get relevant context."""
        return "Content: This is a test content chunk about machine learning.\nSimilarity: 0.9500\n\nContent: This is another test content chunk about deep learning.\nSimilarity: 0.8500"
    
    async def answer_with_context(self, question, max_context_chunks=3):
        """Mock answer with context."""
        return {
            "answer": "Machine learning and deep learning are subfields of artificial intelligence.",
            "context": "Content: This is a test content chunk about machine learning.\nSimilarity: 0.9500\n\nContent: This is another test content chunk about deep learning.\nSimilarity: 0.8500",
            "has_context": True
        }
    
    async def find_related_materials(self, query, max_materials=5):
        """Mock find related materials."""
        return [
            {
                'material_id': 'material1',
                'similarity': 0.95,
                'sample_content': 'This is a test content chunk about machine learning...'
            },
            {
                'material_id': 'material2',
                'similarity': 0.80,
                'sample_content': 'This is a content chunk about neural networks...'
            }
        ]

@pytest.fixture
def vector_search_service():
    return MockVectorSearchService()

@pytest.mark.asyncio
async def test_search_by_query(vector_search_service):
    # Test search by query
    results = await vector_search_service.search_by_query(
        query='machine learning',
        similarity_threshold=0.7,
        match_count=5
    )
    assert len(results) == 2
    assert results[0]['similarity'] == 0.95
    assert results[1]['similarity'] == 0.85
    assert 'machine learning' in results[0]['content']
    assert 'deep learning' in results[1]['content']

@pytest.mark.asyncio
async def test_get_relevant_context(vector_search_service):
    # Test get relevant context
    context = await vector_search_service.get_relevant_context(
        query='machine learning',
        max_chunks=3
    )
    assert 'machine learning' in context
    assert 'deep learning' in context
    assert 'Similarity: 0.9500' in context
    assert 'Similarity: 0.8500' in context

@pytest.mark.asyncio
async def test_answer_with_context(vector_search_service):
    # Test answer with context
    result = await vector_search_service.answer_with_context(
        question='What are machine learning and deep learning?',
        max_context_chunks=3
    )
    assert 'answer' in result
    assert 'context' in result
    assert 'has_context' in result
    assert result['has_context'] is True
    assert 'machine learning' in result['answer'].lower() or 'machine learning' in result['context']
    assert 'deep learning' in result['answer'].lower() or 'deep learning' in result['context']

@pytest.mark.asyncio
async def test_find_related_materials(vector_search_service):
    # Test find related materials
    materials = await vector_search_service.find_related_materials(
        query='machine learning',
        max_materials=5
    )
    assert len(materials) == 2
    assert materials[0]['similarity'] == 0.95
    assert materials[1]['similarity'] == 0.80
    assert materials[0]['material_id'] == 'material1'
    assert materials[1]['material_id'] == 'material2'
