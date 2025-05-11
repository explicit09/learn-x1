import pytest
import asyncio
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

from app.services.context_retrieval import context_retrieval_service

@pytest.fixture
def mock_vector_database_service():
    """Mock the vector database service."""
    with patch('app.services.context_retrieval.vector_database_service') as mock:
        # Mock similarity_search method
        mock.similarity_search.return_value = [
            {
                'id': '1',
                'content': 'This is a test content chunk',
                'material_id': 'material-1',
                'similarity': 0.85
            },
            {
                'id': '2',
                'content': 'Another test content chunk',
                'material_id': 'material-2',
                'similarity': 0.75
            }
        ]
        
        # Mock similarity_search_with_filters method
        mock.similarity_search_with_filters.return_value = [
            {
                'id': '1',
                'content': 'This is a test content chunk',
                'material_id': 'material-1',
                'similarity': 0.85
            }
        ]
        
        yield mock

@pytest.fixture
def mock_openai_service():
    """Mock the OpenAI service."""
    with patch('app.services.context_retrieval.openai_service') as mock:
        # Mock create_embedding method
        mock.create_embedding.return_value = [0.1] * 1536  # Mock embedding vector
        
        # Mock chat_completion method
        mock.chat_completion.return_value = "What is a vector database?\nHow do embeddings work?\nWhat is similarity search?"
        
        yield mock

@pytest.fixture
def mock_prisma():
    """Mock the Prisma client."""
    with patch('app.services.context_retrieval.prisma') as mock:
        # Mock execute_raw method for keyword search
        mock.execute_raw.return_value = [
            ('3', 'Content with keywords', 'material-3')
        ]
        
        # Mock find_many for user interactions
        mock.userinteraction.find_many.return_value = []
        
        # Mock find_unique for learning style
        mock.learningstyle.find_unique.return_value = None
        
        # Mock find_unique for user preferences
        mock.userpreference.find_unique.return_value = None
        
        # Mock find_unique for material
        material_mock = MagicMock()
        material_mock.title = "Test Material"
        mock.material.find_unique.return_value = material_mock
        
        yield mock

@pytest.mark.asyncio
async def test_retrieve_context(mock_vector_database_service, mock_openai_service, mock_prisma):
    """Test retrieving context."""
    # Call the retrieve_context method
    results = await context_retrieval_service.retrieve_context(
        query="test query",
        user_id="user-1"
    )
    
    # Check that the results are as expected
    assert len(results) == 1
    assert results[0]['id'] == '1'
    assert results[0]['content'] == 'This is a test content chunk'
    assert results[0]['similarity'] == 0.85
    
    # Verify that the mock methods were called
    mock_openai_service.create_embedding.assert_called_once_with("test query")
    mock_vector_database_service.similarity_search_with_filters.assert_called_once()

@pytest.mark.asyncio
async def test_retrieve_hybrid_context(mock_vector_database_service, mock_openai_service, mock_prisma):
    """Test retrieving hybrid context."""
    # Call the retrieve_hybrid_context method
    results = await context_retrieval_service.retrieve_hybrid_context(
        query="test query",
        user_id="user-1"
    )
    
    # Check that the results contain both vector and keyword results
    assert len(results) == 2  # 1 from vector search + 1 from keyword search
    
    # First result should be from vector search (higher similarity)
    assert results[0]['id'] == '1'
    assert results[0]['similarity'] == 0.85
    
    # Second result should be from keyword search
    assert results[1]['id'] == '3'
    assert results[1]['similarity'] == 0.5  # Default for keyword results

@pytest.mark.asyncio
async def test_generate_sub_queries(mock_openai_service):
    """Test generating sub-queries."""
    # Call the generate_sub_queries method
    sub_queries = await context_retrieval_service.generate_sub_queries(
        main_query="What are vector databases and how do they work?"
    )
    
    # Check that the sub-queries are as expected
    assert len(sub_queries) == 3
    assert "What is a vector database?" in sub_queries
    assert "How do embeddings work?" in sub_queries
    assert "What is similarity search?" in sub_queries
    
    # Verify that the mock method was called
    mock_openai_service.chat_completion.assert_called_once()

@pytest.mark.asyncio
async def test_retrieve_multi_query_context(mock_vector_database_service, mock_openai_service, mock_prisma):
    """Test retrieving multi-query context."""
    # Mock the retrieve_context method to return different results for different queries
    with patch.object(context_retrieval_service, 'retrieve_context') as mock_retrieve:
        mock_retrieve.side_effect = [
            # Results for main query
            [
                {
                    'id': '1',
                    'content': 'This is a test content chunk',
                    'material_id': 'material-1',
                    'similarity': 0.85
                }
            ],
            # Results for sub-query 1
            [
                {
                    'id': '2',
                    'content': 'Another test content chunk',
                    'material_id': 'material-2',
                    'similarity': 0.75
                }
            ],
            # Results for sub-query 2
            [
                {
                    'id': '3',
                    'content': 'A third test content chunk',
                    'material_id': 'material-3',
                    'similarity': 0.65
                }
            ]
        ]
        
        # Call the retrieve_multi_query_context method
        results = await context_retrieval_service.retrieve_multi_query_context(
            main_query="What are vector databases?",
            sub_queries=["What is a vector database?", "How do embeddings work?"],
            user_id="user-1"
        )
        
        # Check that the results are as expected
        assert len(results) == 3
        assert results[0]['id'] == '1'  # Main query result first
        assert results[1]['id'] == '2'  # Sub-query 1 result
        assert results[2]['id'] == '3'  # Sub-query 2 result
        
        # Verify that the mock method was called for each query
        assert mock_retrieve.call_count == 3

@pytest.mark.asyncio
async def test_format_context_for_llm(mock_prisma):
    """Test formatting context for LLM."""
    # Context chunks to format
    context_chunks = [
        {
            'id': '1',
            'content': 'This is a test content chunk',
            'material_id': 'material-1',
            'similarity': 0.85
        },
        {
            'id': '2',
            'content': 'Another test content chunk',
            'material_id': 'material-2',
            'similarity': 0.75
        }
    ]
    
    # Call the format_context_for_llm method
    formatted_context = await context_retrieval_service.format_context_for_llm(context_chunks)
    
    # Check that the formatted context contains the expected content
    assert "[Context 1] From: Test Material" in formatted_context
    assert "This is a test content chunk" in formatted_context
    assert "[Context 2] From: Test Material" in formatted_context
    assert "Another test content chunk" in formatted_context

@pytest.mark.asyncio
async def test_get_context_for_question(mock_vector_database_service, mock_openai_service, mock_prisma):
    """Test getting context for a question."""
    # Mock the _is_complex_question method to return True
    with patch.object(context_retrieval_service, '_is_complex_question', return_value=True):
        # Mock the generate_sub_queries method
        with patch.object(context_retrieval_service, 'generate_sub_queries', return_value=["sub-query-1", "sub-query-2"]):
            # Mock the retrieve_multi_query_context method
            with patch.object(context_retrieval_service, 'retrieve_multi_query_context') as mock_multi_query:
                mock_multi_query.return_value = [
                    {
                        'id': '1',
                        'content': 'This is a test content chunk',
                        'material_id': 'material-1',
                        'similarity': 0.85
                    }
                ]
                
                # Call the get_context_for_question method
                formatted_context, raw_context = await context_retrieval_service.get_context_for_question(
                    question="What is a complex question?",
                    user_id="user-1"
                )
                
                # Check that the results are as expected
                assert len(raw_context) == 1
                assert raw_context[0]['id'] == '1'
                assert "[Context 1] From: Test Material" in formatted_context
                assert "This is a test content chunk" in formatted_context
                
                # Verify that the mock methods were called
                mock_multi_query.assert_called_once()
