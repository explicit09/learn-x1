# OpenAI API Integration

## Overview

The OpenAI API integration provides a robust interface for interacting with OpenAI's models, including text generation, embeddings, function calling, streaming responses, and vision capabilities. This service is designed to be reliable, efficient, and easy to use within the LEARN-X platform.

## Features

### Text Completion

The service provides methods for generating text completions using OpenAI's chat models. It supports system messages, temperature control, and token limits.

### Function Calling

The integration supports OpenAI's function calling capability, allowing the AI to choose to call a function with specific arguments based on the user's input.

### Streaming Responses

For long-form responses or real-time interactions, the service provides streaming capabilities that yield chunks of the generated text as they become available.

### Image Processing

The integration includes support for OpenAI's vision models, allowing the processing of images along with text prompts.

### Embeddings Generation

The service can generate vector embeddings for text, which are used for semantic search and retrieval in the vector database.

### Quiz Generation

The integration includes specialized methods for generating quiz questions from educational content, supporting multiple question types and difficulty levels.

## Usage Examples

### Text Completion

```python
from app.services.openai import openai_service

async def example_completion():
    response = await openai_service.generate_completion(
        prompt="Explain the concept of machine learning in simple terms.",
        system_message="You are a helpful educational assistant.",
        temperature=0.7,
        max_tokens=500
    )
    
    print(response)
```

### Function Calling

```python
from app.services.openai import openai_service

async def example_function_calling():
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
    
    response = await openai_service.generate_completion_with_functions(
        prompt="What's the weather in Paris?",
        functions=functions,
        function_call="auto"
    )
    
    if response["function_call"]:
        function_name = response["function_call"]["name"]
        function_args = response["function_call"]["arguments"]
        print(f"Function: {function_name}, Arguments: {function_args}")
    else:
        print(response["content"])
```

### Streaming Responses

```python
from app.services.openai import openai_service

async def example_streaming():
    async for chunk in openai_service.generate_streaming_completion(
        prompt="Write a short story about a robot learning to paint.",
        max_tokens=1000
    ):
        print(chunk, end="", flush=True)
```

### Image Processing

```python
from app.services.openai import openai_service

async def example_image_processing():
    response = await openai_service.process_image(
        image_url="https://example.com/image.jpg",
        prompt="Describe what you see in this image in detail."
    )
    
    print(response)
```

### Embeddings Generation

```python
from app.services.openai import openai_service

async def example_embeddings():
    texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Natural language processing deals with interactions between computers and human language."
    ]
    
    embeddings = await openai_service.generate_embeddings(texts)
    
    print(f"Generated {len(embeddings)} embeddings, each with {len(embeddings[0])} dimensions.")
```

### Quiz Generation

```python
from app.services.openai import openai_service

async def example_quiz_generation():
    content = """
    The solar system consists of the Sun and everything that orbits around it, including planets, moons, asteroids, and comets.
    There are eight planets in our solar system: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.
    The four inner planets (Mercury, Venus, Earth, and Mars) are called terrestrial planets because they have solid, rocky surfaces.
    The four outer planets (Jupiter, Saturn, Uranus, and Neptune) are called gas giants because they are large and composed mainly of gas.
    """
    
    questions = await openai_service.generate_quiz_questions(
        content=content,
        num_questions=3,
        question_types=["multiple_choice", "true_false"],
        difficulty="medium"
    )
    
    for i, question in enumerate(questions, 1):
        print(f"Question {i}: {question['question_text']}")
        if question['question_type'] == 'multiple_choice':
            for j, option in enumerate(question['options']):
                print(f"  {chr(65+j)}. {option}")
        print(f"Correct answer: {question['correct_answer']}")
        print(f"Explanation: {question['explanation']}\n")
```

## Configuration

The OpenAI integration uses the following environment variables:

- `OPENAI_API_KEY`: API key for OpenAI services (required)
- `OPENAI_MODEL`: Model to use for chat completions (default: gpt-4)
- `OPENAI_EMBEDDING_MODEL`: Model to use for embeddings (default: text-embedding-3-small)
- `OPENAI_VISION_MODEL`: Model to use for vision capabilities (default: gpt-4-vision-preview)

## Error Handling

The service includes robust error handling with automatic retries for rate limits and transient errors. It uses exponential backoff to avoid overwhelming the API during rate limiting.

Common errors include:

- `ValueError`: Raised when the API key is not configured
- `openai.RateLimitError`: Raised when the API rate limit is exceeded (automatically retried)
- `openai.APIError`: Raised when there's an error from the OpenAI API

## Performance Considerations

- **Response Time**: API calls may take several seconds to complete, especially for longer generations
- **Rate Limits**: The service includes built-in rate limiting handling, but be mindful of your OpenAI account's limits
- **Token Usage**: Monitor token usage to control costs, especially for high-volume applications
- **Streaming**: Use streaming for long-form responses to improve user experience

## Security

- The API key is securely stored in environment variables and never exposed to clients
- User data is processed according to OpenAI's data usage policies
- Consider implementing additional content filtering for user inputs

## Future Enhancements

- Support for fine-tuned models
- Integration with OpenAI's assistants API
- Enhanced caching for common queries
- Support for multi-modal inputs and outputs
