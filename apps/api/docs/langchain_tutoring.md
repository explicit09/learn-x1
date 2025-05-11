# LangChain Tutoring Integration

## Overview

The LangChain Tutoring integration enhances the AI tutoring capabilities of the LEARN-X platform by leveraging the LangChain framework. This integration provides more powerful context-aware responses, improved conversational abilities, and advanced tutoring features.

## Features

### Context-Aware Question Answering

The LangChain tutoring system uses vector embeddings stored in the PostgreSQL database (via pgvector) to retrieve relevant context for user questions. This allows the AI tutor to provide more accurate and informative responses based on course materials.

### Multiple Tutoring Modes

The system supports different tutoring modes to accommodate various learning styles and needs:

- **Default**: Balanced approach suitable for most learners
- **Beginner**: Simplified explanations with analogies and examples
- **Advanced**: Detailed technical explanations for advanced learners
- **Socratic**: Guides students through questioning rather than direct answers

### Personalized Study Plans

The LangChain tutoring system can generate personalized study plans based on specific topics and learning goals. These plans include daily activities, recommended resources, and self-assessment methods.

### Answer Assessment

The system can evaluate student answers to questions, providing constructive feedback, correctness scores, and suggestions for improvement.

## API Endpoints

### Answer Question

```
POST /api/langchain-tutoring/question
```

**Request Body:**

```json
{
  "question": "What is the difference between supervised and unsupervised learning?",
  "chat_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there! How can I help you?"}
  ],
  "tutoring_mode": "default",
  "course_id": "course123",
  "confusion_level": 3
}
```

**Response:**

```json
{
  "answer": "Supervised learning uses labeled data where the algorithm learns to map inputs to outputs, while unsupervised learning works with unlabeled data to find patterns or structure...",
  "has_context": true,
  "tutoring_mode": "default",
  "timestamp": "2025-05-09T14:30:45.123456"
}
```

### Explain Concept

```
POST /api/langchain-tutoring/explain
```

**Request Body:**

```json
{
  "concept": "Neural Networks",
  "detail_level": "medium",
  "course_id": "course123"
}
```

**Response:**

```json
{
  "concept": "Neural Networks",
  "explanation": "Neural networks are computational models inspired by the human brain...",
  "detail_level": "medium",
  "has_context": true,
  "timestamp": "2025-05-09T14:32:10.123456"
}
```

### Generate Study Plan

```
POST /api/langchain-tutoring/study-plan
```

**Request Body:**

```json
{
  "topic": "Machine Learning",
  "learning_goal": "Build a recommendation system",
  "duration_days": 14,
  "course_id": "course123"
}
```

**Response:**

```json
{
  "topic": "Machine Learning",
  "learning_goal": "Build a recommendation system",
  "duration_days": 14,
  "study_plan": "Day 1: Introduction to recommendation systems...\nDay 2: Data preprocessing techniques...",
  "has_context": true,
  "timestamp": "2025-05-09T14:35:22.123456"
}
```

### Assess Answer

```
POST /api/langchain-tutoring/assess
```

**Request Body:**

```json
{
  "question": "Explain the concept of backpropagation in neural networks.",
  "student_answer": "Backpropagation is an algorithm used to train neural networks by calculating gradients and updating weights to minimize error.",
  "course_id": "course123"
}
```

**Response:**

```json
{
  "question": "Explain the concept of backpropagation in neural networks.",
  "student_answer": "Backpropagation is an algorithm used to train neural networks by calculating gradients and updating weights to minimize error.",
  "assessment": "Feedback: Good basic explanation of backpropagation.\nScore: 75/100\nSuggestions: Consider explaining the chain rule's role and how errors propagate backward through the network.",
  "has_context": true,
  "timestamp": "2025-05-09T14:38:05.123456"
}
```

## Implementation Details

### Architecture

The LangChain tutoring system consists of several components:

1. **LangChainTutoringService**: Core service that handles interactions with LangChain and OpenAI
2. **Vector Database**: PostgreSQL with pgvector extension for storing and retrieving embeddings
3. **Content Chunking**: Service for breaking down materials into appropriate chunks for embedding
4. **API Routes**: FastAPI endpoints for exposing the tutoring functionality

### Dependencies

- LangChain framework
- OpenAI API
- PostgreSQL with pgvector extension
- FastAPI

### Configuration

The LangChain tutoring system uses the following environment variables:

- `OPENAI_API_KEY`: API key for OpenAI services
- `OPENAI_MODEL`: Model to use for chat completions (default: gpt-4)
- `OPENAI_EMBEDDING_MODEL`: Model to use for embeddings (default: text-embedding-3-small)

## Performance Considerations

- **Response Time**: The system performs vector similarity searches and LLM calls, which may take a few seconds to complete
- **Cost Optimization**: The system uses the vector database to retrieve relevant context, reducing the need for large context windows
- **Caching**: Consider implementing response caching for common questions to improve performance

## Security

- All endpoints require authentication
- User data is isolated by organization using Row-Level Security (RLS) policies
- API keys are securely stored and never exposed to clients

## Future Enhancements

- **Streaming Responses**: Implement streaming for long-form responses
- **Multi-modal Support**: Add support for images and diagrams in explanations
- **Feedback Loop**: Incorporate user feedback to improve responses over time
- **Custom Knowledge Base**: Allow organizations to upload their own materials for tutoring
