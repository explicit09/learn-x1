import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import openai
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.embedding import Embedding
from app.services.openai import OpenAIService, OpenAIError
from app.core.config import settings

@pytest.fixture
def openai_service():
    with patch.object(settings, 'OPENAI_API_KEY', 'test-api-key'):
        service = OpenAIService()
        return service

@pytest.fixture
def mock_openai_client():
    with patch('app.services.openai.AsyncOpenAI') as mock_client:
        # Create a mock instance that will be returned when AsyncOpenAI is instantiated
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Setup chat.completions.create mock
        mock_instance.chat.completions.create = AsyncMock()
        
        # Setup embeddings.create mock
        mock_instance.embeddings.create = AsyncMock()
        
        yield mock_instance

@pytest.mark.asyncio
async def test_generate_completion(openai_service, mock_openai_client):
    # Setup mock response
    mock_message = ChatCompletionMessage(role="assistant", content="This is a test response")
    mock_response = ChatCompletion(
        id="cmpl-123",
        choices=[MagicMock(message=mock_message, finish_reason="stop")],
        created=1677858242,
        model="gpt-4",
        object="chat.completion",
        usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    )
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Test the generate_completion method
    result = await openai_service.generate_completion(
        messages=[{"role": "user", "content": "Hello, world!"}],
        model="gpt-4"
    )
    
    # Verify the result
    assert result["content"] == "This is a test response"
    assert result["tokens_used"] == 30
    
    # Verify the OpenAI client was called with the correct parameters
    mock_openai_client.chat.completions.create.assert_called_once()
    call_args = mock_openai_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-4"
    assert call_args["messages"] == [{"role": "user", "content": "Hello, world!"}]

@pytest.mark.asyncio
async def test_generate_completion_error(openai_service, mock_openai_client):
    # Setup mock to raise an exception
    mock_openai_client.chat.completions.create.side_effect = openai.RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429),
        body=json.dumps({"error": {"message": "Rate limit exceeded"}})
    )
    
    # Test the generate_completion method with an error
    with pytest.raises(OpenAIError) as excinfo:
        await openai_service.generate_completion(
            messages=[{"role": "user", "content": "Hello, world!"}],
            model="gpt-4"
        )
    
    # Verify the error message
    assert "Rate limit exceeded" in str(excinfo.value)
    assert excinfo.value.status_code == 429

@pytest.mark.asyncio
async def test_generate_embedding(openai_service, mock_openai_client):
    # Setup mock response
    mock_response = MagicMock(
        data=[MagicMock(embedding=[0.1, 0.2, 0.3, 0.4])],
        model="text-embedding-ada-002",
        usage=MagicMock(prompt_tokens=5, total_tokens=5)
    )
    mock_openai_client.embeddings.create.return_value = mock_response
    
    # Test the generate_embedding method
    result = await openai_service.generate_embedding("Hello, world!")
    
    # Verify the result
    assert result["embedding"] == [0.1, 0.2, 0.3, 0.4]
    assert result["tokens_used"] == 5
    
    # Verify the OpenAI client was called with the correct parameters
    mock_openai_client.embeddings.create.assert_called_once()
    call_args = mock_openai_client.embeddings.create.call_args[1]
    assert call_args["model"] == "text-embedding-ada-002"
    assert call_args["input"] == "Hello, world!"

@pytest.mark.asyncio
async def test_generate_embedding_error(openai_service, mock_openai_client):
    # Setup mock to raise an exception
    mock_openai_client.embeddings.create.side_effect = openai.APIError(
        message="API error",
        response=MagicMock(status_code=500),
        body=json.dumps({"error": {"message": "Internal server error"}})
    )
    
    # Test the generate_embedding method with an error
    with pytest.raises(OpenAIError) as excinfo:
        await openai_service.generate_embedding("Hello, world!")
    
    # Verify the error message
    assert "API error" in str(excinfo.value)
    assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_generate_quiz_questions(openai_service):
    # Mock the generate_completion method
    with patch.object(openai_service, 'generate_completion', new_callable=AsyncMock) as mock_generate:
        # Setup mock response
        mock_generate.return_value = {
            "content": json.dumps([
                {
                    "question": "What is the capital of France?",
                    "options": ["Paris", "London", "Berlin", "Madrid"],
                    "answer": "Paris",
                    "explanation": "Paris is the capital of France."
                },
                {
                    "question": "What is 2+2?",
                    "options": ["3", "4", "5", "6"],
                    "answer": "4",
                    "explanation": "2+2=4"
                }
            ]),
            "tokens_used": 100
        }
        
        # Test the generate_quiz_questions method
        result = await openai_service.generate_quiz_questions(
            content="France is a country in Europe. Its capital is Paris.",
            num_questions=2,
            question_types=["multiple_choice"],
            difficulty="medium"
        )
        
        # Verify the result
        assert len(result) == 2
        assert result[0]["question"] == "What is the capital of France?"
        assert result[1]["question"] == "What is 2+2?"
        
        # Verify generate_completion was called with the correct parameters
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[1]
        assert call_args["model"] == "gpt-4"
        assert any("France is a country in Europe" in msg["content"] for msg in call_args["messages"])
        assert any("2 questions" in msg["content"] for msg in call_args["messages"])
        assert any("multiple_choice" in msg["content"] for msg in call_args["messages"])
        assert any("medium difficulty" in msg["content"] for msg in call_args["messages"])

@pytest.mark.asyncio
async def test_generate_quiz_questions_invalid_json(openai_service):
    # Mock the generate_completion method to return invalid JSON
    with patch.object(openai_service, 'generate_completion', new_callable=AsyncMock) as mock_generate:
        # Setup mock response with invalid JSON
        mock_generate.return_value = {
            "content": "This is not valid JSON",
            "tokens_used": 50
        }
        
        # Test the generate_quiz_questions method with invalid JSON
        with pytest.raises(OpenAIError) as excinfo:
            await openai_service.generate_quiz_questions(
                content="Test content",
                num_questions=2
            )
        
        # Verify the error message
        assert "Failed to parse quiz questions" in str(excinfo.value)

@pytest.mark.asyncio
async def test_api_key_not_set():
    # Test creating the service with no API key
    with patch.object(settings, 'OPENAI_API_KEY', None):
        with pytest.raises(OpenAIError) as excinfo:
            OpenAIService()
        
        # Verify the error message
        assert "OpenAI API key is not set" in str(excinfo.value)

@pytest.mark.asyncio
async def test_custom_system_message(openai_service):
    # Mock the generate_completion method
    with patch.object(openai_service, 'generate_completion', new_callable=AsyncMock) as mock_generate:
        # Setup mock response
        mock_generate.return_value = {
            "content": "Custom response",
            "tokens_used": 30
        }
        
        # Test with a custom system message
        await openai_service.generate_completion(
            messages=[{"role": "user", "content": "Hello"}],
            system_message="You are a custom assistant"
        )
        
        # Verify the system message was included
        call_args = mock_generate.call_args[1]
        messages = call_args["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a custom assistant"

@pytest.mark.asyncio
async def test_temperature_setting(openai_service, mock_openai_client):
    # Setup mock response
    mock_message = ChatCompletionMessage(role="assistant", content="Response")
    mock_response = ChatCompletion(
        id="cmpl-123",
        choices=[MagicMock(message=mock_message, finish_reason="stop")],
        created=1677858242,
        model="gpt-4",
        object="chat.completion",
        usage=MagicMock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
    )
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Test with custom temperature
    await openai_service.generate_completion(
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.2
    )
    
    # Verify the temperature was set correctly
    call_args = mock_openai_client.chat.completions.create.call_args[1]
    assert call_args["temperature"] == 0.2
