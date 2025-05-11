import pytest
import os
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.openai import OpenAIService

# Skip tests if no OpenAI API key is available
pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OpenAI API key not available"
)

@pytest.fixture
def openai_service():
    """Create an OpenAIService instance with mocked clients."""
    service = OpenAIService()
    
    # Mock the async client
    service.async_client = AsyncMock()
    
    # Mock the chat completions create method
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "This is a mock response from OpenAI."
    mock_response.choices[0].message.function_call = None
    
    service.async_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Mock the embeddings create method
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [
        MagicMock(embedding=[0.1, 0.2, 0.3]),
        MagicMock(embedding=[0.4, 0.5, 0.6])
    ]
    
    service.async_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)
    
    return service

@pytest.mark.asyncio
async def test_generate_completion(openai_service):
    """Test generating a completion."""
    # Call the method
    result = await openai_service.generate_completion(
        prompt="What is the capital of France?",
        system_message="You are a helpful assistant."
    )
    
    # Assertions
    assert result == "This is a mock response from OpenAI."
    assert openai_service.async_client.chat.completions.create.called
    
    # Check that the correct arguments were passed
    call_args = openai_service.async_client.chat.completions.create.call_args[1]
    assert call_args["model"] == openai_service.model
    assert len(call_args["messages"]) == 2
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][1]["role"] == "user"

@pytest.mark.asyncio
async def test_generate_completion_with_functions(openai_service):
    """Test generating a completion with function calling."""
    # Mock function call response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.function_call = MagicMock()
    mock_response.choices[0].message.function_call.name = "get_weather"
    mock_response.choices[0].message.function_call.arguments = '{"location": "Paris", "unit": "celsius"}'
    
    openai_service.async_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Test data
    functions = [
        {
            "name": "get_weather",
            "description": "Get the weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    ]
    
    # Call the method
    result = await openai_service.generate_completion_with_functions(
        prompt="What's the weather in Paris?",
        functions=functions,
        function_call="auto"
    )
    
    # Assertions
    assert result["content"] is None
    assert result["function_call"] is not None
    assert result["function_call"]["name"] == "get_weather"
    assert result["function_call"]["arguments"]["location"] == "Paris"
    assert result["function_call"]["arguments"]["unit"] == "celsius"

@pytest.mark.asyncio
async def test_generate_streaming_completion(openai_service):
    """Test generating a streaming completion."""
    # Mock streaming response
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta = MagicMock()
    chunk1.choices[0].delta.content = "Hello"
    
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta = MagicMock()
    chunk2.choices[0].delta.content = " world"
    
    chunk3 = MagicMock()
    chunk3.choices = [MagicMock()]
    chunk3.choices[0].delta = MagicMock()
    chunk3.choices[0].delta.content = "!"
    
    # Create an async generator for the mock response
    async def mock_stream():
        yield chunk1
        yield chunk2
        yield chunk3
    
    openai_service.async_client.chat.completions.create = AsyncMock(return_value=mock_stream())
    
    # Call the method
    chunks = []
    async for chunk in openai_service.generate_streaming_completion(prompt="Hello?"):
        chunks.append(chunk)
    
    # Assertions
    assert chunks == ["Hello", " world", "!"]

@pytest.mark.asyncio
async def test_process_image(openai_service):
    """Test processing an image."""
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "This is an image of the Eiffel Tower in Paris."
    
    openai_service.async_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Call the method
    result = await openai_service.process_image(
        image_url="https://example.com/eiffel_tower.jpg",
        prompt="What's in this image?"
    )
    
    # Assertions
    assert result == "This is an image of the Eiffel Tower in Paris."
    assert openai_service.async_client.chat.completions.create.called
    
    # Check that the correct arguments were passed
    call_args = openai_service.async_client.chat.completions.create.call_args[1]
    assert call_args["model"] == openai_service.vision_model
    assert len(call_args["messages"]) == 1
    assert call_args["messages"][0]["role"] == "user"
    assert len(call_args["messages"][0]["content"]) == 2
    assert call_args["messages"][0]["content"][0]["type"] == "text"
    assert call_args["messages"][0]["content"][1]["type"] == "image_url"

@pytest.mark.asyncio
async def test_generate_embeddings(openai_service):
    """Test generating embeddings."""
    # Call the method
    result = await openai_service.generate_embeddings(["Hello", "World"])
    
    # Assertions
    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3]
    assert result[1] == [0.4, 0.5, 0.6]
    assert openai_service.async_client.embeddings.create.called
    
    # Check that the correct arguments were passed
    call_args = openai_service.async_client.embeddings.create.call_args[1]
    assert call_args["model"] == openai_service.embedding_model
    assert call_args["input"] == ["Hello", "World"]

@pytest.mark.asyncio
async def test_generate_quiz_questions(openai_service):
    """Test generating quiz questions."""
    # Mock response for quiz questions
    mock_questions = [
        {
            "question_text": "What is the capital of France?",
            "question_type": "multiple_choice",
            "options": ["Paris", "London", "Berlin", "Madrid"],
            "correct_answer": "Paris",
            "explanation": "Paris is the capital of France."
        },
        {
            "question_text": "The Eiffel Tower is located in Paris.",
            "question_type": "true_false",
            "correct_answer": True,
            "explanation": "The Eiffel Tower is indeed located in Paris, France."
        }
    ]
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = '{"questions": ' + str(mock_questions).replace("'", "\"").replace("True", "true") + '}'
    
    openai_service.async_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Call the method
    result = await openai_service.generate_quiz_questions(
        content="France is a country in Western Europe. Its capital is Paris, where the Eiffel Tower is located.",
        num_questions=2
    )
    
    # Assertions
    assert len(result) == 2
    assert result[0]["question_text"] == "What is the capital of France?"
    assert result[0]["question_type"] == "multiple_choice"
    assert result[1]["question_text"] == "The Eiffel Tower is located in Paris."
    assert result[1]["question_type"] == "true_false"
