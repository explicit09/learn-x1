import os
import time
import json
from typing import List, Dict, Any, Optional, Union, Callable, AsyncGenerator
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai
from openai import OpenAI, AsyncOpenAI

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OpenAI API key not found. AI features will not work.")
        
        # Initialize synchronous and asynchronous clients
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        
        # Default models and settings
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.vision_model = getattr(settings, 'OPENAI_VISION_MODEL', 'gpt-4-vision-preview')
        self.max_retries = 3
        self.request_timeout = 60  # seconds
        
        # Rate limiting settings
        self.rate_limit_min_pause = 0.1  # minimum pause between requests in seconds
        self.rate_limit_backoff = 2.0  # exponential backoff factor for rate limits
    
    @retry(retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
           stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_completion(self, prompt: str, system_message: str = None, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text completion using OpenAI API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.request_timeout
            )
            
            return response.choices[0].message.content
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}. Retrying with exponential backoff.")
            time.sleep(self.rate_limit_min_pause * self.rate_limit_backoff)
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            raise
            
    async def generate_completion_with_functions(
        self, 
        prompt: str, 
        functions: List[Dict[str, Any]], 
        system_message: str = None, 
        temperature: float = 0.7, 
        max_tokens: int = 1000,
        function_call: str = "auto"
    ) -> Dict[str, Any]:
        """Generate text completion with function calling capabilities.
        
        Args:
            prompt: The user prompt
            functions: List of function definitions in OpenAI format
            system_message: Optional system message
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            function_call: Control function calling ("auto", "none", or {"name": "function_name"})
            
        Returns:
            Dictionary with response content and function call details if applicable
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                functions=functions,
                function_call=function_call,
                timeout=self.request_timeout
            )
            
            message = response.choices[0].message
            result = {
                "content": message.content,
                "function_call": None
            }
            
            # Handle function call if present
            if hasattr(message, 'function_call') and message.function_call:
                result["function_call"] = {
                    "name": message.function_call.name,
                    "arguments": json.loads(message.function_call.arguments)
                }
                
            return result
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}. Retrying with exponential backoff.")
            time.sleep(self.rate_limit_min_pause * self.rate_limit_backoff)
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating completion with functions: {str(e)}")
            raise
            
    async def generate_streaming_completion(
        self, 
        prompt: str, 
        system_message: str = None, 
        temperature: float = 0.7, 
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text completion using OpenAI API.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of the generated text as they become available
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            messages.append({"role": "user", "content": prompt})
            
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.request_timeout,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}. Retrying with exponential backoff.")
            time.sleep(self.rate_limit_min_pause * self.rate_limit_backoff)
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating streaming completion: {str(e)}")
            raise
            
    async def process_image(
        self, 
        image_url: str, 
        prompt: str, 
        system_message: str = None, 
        temperature: float = 0.7, 
        max_tokens: int = 1000
    ) -> str:
        """Process an image and generate a response using OpenAI's vision capabilities.
        
        Args:
            image_url: URL of the image to process (can be a local file:// URL)
            prompt: The user prompt about the image
            system_message: Optional system message
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response about the image
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add the image and prompt to the user message
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            })
            
            response = await self.async_client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.request_timeout
            )
            
            return response.choices[0].message.content
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}. Retrying with exponential backoff.")
            time.sleep(self.rate_limit_min_pause * self.rate_limit_backoff)
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise
    
    @retry(retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
           stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            response = await self.async_client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                timeout=self.request_timeout
            )
            
            return [data.embedding for data in response.data]
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}. Retrying with exponential backoff.")
            time.sleep(self.rate_limit_min_pause * self.rate_limit_backoff)
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    @retry(retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
           stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_quiz_questions(self, content: str, num_questions: int = 5, question_types: List[str] = None, difficulty: str = "medium", system_message: str = None) -> List[Dict[str, Any]]:
        """Generate quiz questions from content.
        
        Args:
            content: The content to generate questions from
            num_questions: Number of questions to generate
            question_types: Types of questions to generate (multiple_choice, true_false, etc.)
            difficulty: Difficulty level (easy, medium, hard)
            system_message: Optional custom system message for quiz generation
            
        Returns:
            List of generated quiz questions
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        if question_types is None:
            question_types = ["multiple_choice", "true_false"]
        
        # Use provided system message or default
        if not system_message:
            system_message = f"""
            You are an expert quiz generator for educational content. 
            Generate {num_questions} {difficulty} difficulty questions based on the provided content.
            Use the following question types: {', '.join(question_types)}.
            
            For multiple choice questions, provide 4 options with 1 correct answer.
            For true/false questions, provide a statement and whether it's true or false.
            
            Return the questions in the following JSON format:
            [
                {{
                    "question_text": "Question text",
                    "question_type": "multiple_choice",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Explanation of the correct answer"
                }},
                {{
                    "question_text": "Statement",
                    "question_type": "true_false",
                    "correct_answer": true,
                    "explanation": "Explanation of why the statement is true/false"
                }}
            ]
            """
        
        try:
            user_content = f"Content: {content}\n\nGenerate quiz questions based on this content."
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
                timeout=self.request_timeout
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON string to Python object
            try:
                parsed_result = json.loads(result)
                
                # Handle different possible JSON structures
                if "questions" in parsed_result:
                    questions = parsed_result["questions"]
                elif isinstance(parsed_result, list):
                    questions = parsed_result
                else:
                    # Try to find any list in the response
                    for key, value in parsed_result.items():
                        if isinstance(value, list) and len(value) > 0:
                            questions = value
                            break
                    else:
                        questions = []
                        logger.warning(f"Unexpected JSON structure in quiz generation: {result}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing quiz questions JSON: {str(e)}")
                questions = []
                
            return questions
            
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}. Retrying with exponential backoff.")
            time.sleep(self.rate_limit_min_pause * self.rate_limit_backoff)
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating quiz questions: {str(e)}")
            raise

# Create a singleton instance of the OpenAIService
openai_service = OpenAIService()
