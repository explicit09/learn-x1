import pytest
import os
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.langchain_tutoring import LangChainTutoringService

# Skip tests if no OpenAI API key is available
pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OpenAI API key not available"
)

@pytest.fixture
def mock_vector_search_service():
    """Create a mock vector search service."""
    mock_service = AsyncMock()
    mock_service.get_relevant_context = AsyncMock(return_value="This is mock context for testing.")
    return mock_service

@pytest.fixture
def langchain_tutoring_service(mock_vector_search_service):
    """Create a LangChainTutoringService instance with mocked dependencies."""
    with patch("app.services.langchain_tutoring.vector_search_service", mock_vector_search_service):
        service = LangChainTutoringService()
        # Mock the chat model to avoid actual API calls
        mock_chat_model = AsyncMock()
        mock_chat_model.ainvoke = AsyncMock(return_value="This is a mock response from the LLM.")
        service.chat_model = mock_chat_model
        yield service

@pytest.mark.asyncio
async def test_answer_question(langchain_tutoring_service):
    """Test answering a question with LangChain."""
    # Test data
    question = "What is the capital of France?"
    chat_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"}
    ]
    
    # Mock the chain invoke method
    langchain_tutoring_service.chat_model.ainvoke = AsyncMock(return_value="Paris is the capital of France.")
    
    # Call the method
    result = await langchain_tutoring_service.answer_question(
        question=question,
        chat_history=chat_history,
        tutoring_mode="default"
    )
    
    # Assertions
    assert result["answer"] == "Paris is the capital of France."
    assert result["has_context"] == True
    assert result["tutoring_mode"] == "default"
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_explain_concept(langchain_tutoring_service):
    """Test explaining a concept with LangChain."""
    # Test data
    concept = "Machine Learning"
    
    # Mock the chain invoke method
    langchain_tutoring_service.chat_model.ainvoke = AsyncMock(
        return_value="Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
    )
    
    # Call the method
    result = await langchain_tutoring_service.explain_concept(
        concept=concept,
        detail_level="medium"
    )
    
    # Assertions
    assert result["concept"] == "Machine Learning"
    assert "Machine Learning is a subset of artificial intelligence" in result["explanation"]
    assert result["detail_level"] == "medium"
    assert result["has_context"] == True
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_generate_study_plan(langchain_tutoring_service):
    """Test generating a study plan with LangChain."""
    # Test data
    topic = "Python Programming"
    learning_goal = "Become proficient in Python web development"
    
    # Mock the chain invoke method
    langchain_tutoring_service.chat_model.ainvoke = AsyncMock(
        return_value="Day 1: Introduction to Python\nDay 2: Basic syntax and data types\nDay 3: Control structures\nDay 4: Functions and modules\nDay 5: Object-oriented programming\nDay 6: Web frameworks\nDay 7: Building a simple web application"
    )
    
    # Call the method
    result = await langchain_tutoring_service.generate_study_plan(
        topic=topic,
        learning_goal=learning_goal,
        duration_days=7
    )
    
    # Assertions
    assert result["topic"] == "Python Programming"
    assert result["learning_goal"] == "Become proficient in Python web development"
    assert result["duration_days"] == 7
    assert "Day 1: Introduction to Python" in result["study_plan"]
    assert result["has_context"] == True
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_assess_answer(langchain_tutoring_service):
    """Test assessing a student's answer with LangChain."""
    # Test data
    question = "What are the key principles of object-oriented programming?"
    student_answer = "Object-oriented programming is based on encapsulation, inheritance, and polymorphism."
    
    # Mock the chain invoke method
    langchain_tutoring_service.chat_model.ainvoke = AsyncMock(
        return_value="Feedback: Good answer that identifies the three main principles.\nScore: 85/100\nSuggestions: Consider also mentioning abstraction as a key principle."
    )
    
    # Call the method
    result = await langchain_tutoring_service.assess_answer(
        question=question,
        student_answer=student_answer
    )
    
    # Assertions
    assert result["question"] == question
    assert result["student_answer"] == student_answer
    assert "Feedback: Good answer" in result["assessment"]
    assert result["has_context"] == True
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_error_handling(langchain_tutoring_service):
    """Test error handling in the LangChain tutoring service."""
    # Mock the get_relevant_context method to raise an exception
    langchain_tutoring_service._get_relevant_context = AsyncMock(side_effect=Exception("Test error"))
    
    # Call the method
    result = await langchain_tutoring_service.answer_question(
        question="What is the capital of France?"
    )
    
    # Assertions
    assert "error" in result
    assert "Test error" in result["answer"]
    assert result["has_context"] == False
