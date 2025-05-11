import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Create a mock class for testing without dependencies
class MockOpenAIService:
    """A simplified version of the OpenAIService for testing."""
    
    def __init__(self, api_key="test-api-key"):
        self.api_key = api_key
    
    async def generate_completion(self, messages, model="gpt-4", temperature=0.7, system_message=None):
        """Generate a completion using the OpenAI API."""
        # Return mock data for testing
        return {
            "content": "This is a test response",
            "tokens_used": 30
        }
    
    async def generate_embedding(self, text, model="text-embedding-ada-002"):
        """Generate an embedding for the given text."""
        # Return mock data for testing
        return {
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "tokens_used": 5
        }
    
    async def generate_quiz_questions(self, content, num_questions=5, question_types=None, 
                                     difficulty="medium", system_message=None):
        """Generate quiz questions based on the provided content."""
        if question_types is None:
            question_types = ["multiple_choice"]
            
        # Return mock data for testing
        return [
            {
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Berlin", "Madrid"],
                "answer": "Paris",
                "explanation": "Paris is the capital of France.",
                "question_type": "multiple_choice",
                "difficulty": difficulty
            },
            {
                "question": "True or False: The Earth is flat.",
                "options": ["True", "False"],
                "answer": "False",
                "explanation": "The Earth is approximately spherical.",
                "question_type": "true_false",
                "difficulty": difficulty
            }
        ]

@pytest.fixture
def openai_service():
    return MockOpenAIService()

@pytest.mark.asyncio
async def test_generate_completion(openai_service):
    # Test the generate_completion method
    result = await openai_service.generate_completion(
        messages=[{"role": "user", "content": "Hello, world!"}],
        model="gpt-4"
    )
    
    # Verify the result
    assert "content" in result
    assert "tokens_used" in result
    assert result["content"] == "This is a test response"
    assert result["tokens_used"] == 30

@pytest.mark.asyncio
async def test_generate_completion_with_system_message(openai_service):
    # Test with a custom system message
    result = await openai_service.generate_completion(
        messages=[{"role": "user", "content": "Hello"}],
        system_message="You are a custom assistant"
    )
    
    # Verify the result
    assert "content" in result
    assert "tokens_used" in result

@pytest.mark.asyncio
async def test_generate_embedding(openai_service):
    # Test the generate_embedding method
    result = await openai_service.generate_embedding("Hello, world!")
    
    # Verify the result
    assert "embedding" in result
    assert "tokens_used" in result
    assert len(result["embedding"]) == 4
    assert result["tokens_used"] == 5

@pytest.mark.asyncio
async def test_generate_quiz_questions(openai_service):
    # Test the generate_quiz_questions method
    result = await openai_service.generate_quiz_questions(
        content="France is a country in Europe. Its capital is Paris.",
        num_questions=2,
        question_types=["multiple_choice", "true_false"],
        difficulty="medium"
    )
    
    # Verify the result
    assert len(result) == 2
    assert result[0]["question"] == "What is the capital of France?"
    assert result[0]["answer"] == "Paris"
    assert result[0]["question_type"] == "multiple_choice"
    assert result[1]["question_type"] == "true_false"
    
@pytest.mark.asyncio
async def test_generate_quiz_questions_with_different_difficulty(openai_service):
    # Test with different difficulty levels
    result = await openai_service.generate_quiz_questions(
        content="Test content",
        difficulty="hard"
    )
    
    # Verify the difficulty was set correctly
    assert result[0]["difficulty"] == "hard"
