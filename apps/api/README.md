# LEARN-X API

This is the API implementation for the LEARN-X educational platform. The API is built using FastAPI and integrates with the PostgreSQL database using Prisma ORM.

## Features

- Authentication and authorization with JWT tokens
- Multi-tenant architecture with organization isolation
- Role-based access control (student, professor, admin)
- Course and content management
- Quiz system with various question types
- AI-powered tutoring and content search
- Vector embeddings for semantic search

## Project Structure

```
/app
  /api
    /routes         # API endpoint routes
  /core            # Core configuration
  /db              # Database models and connection
  /schemas         # Pydantic schemas for request/response validation
  /services        # Business logic services
  main.py         # FastAPI application entry point
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL with pgvector extension
- Node.js (for Prisma CLI)

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:

```
DATABASE_URL="postgresql://username:password@localhost:5432/learnx"
DIRECT_URL="postgresql://username:password@localhost:5432/learnx"
JWT_SECRET="your-secret-key"
OPENAI_API_KEY="your-openai-api-key"
```

3. Run the API server:

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Authentication

The API uses JWT token-based authentication. To access protected endpoints:

1. Register a user with `/api/auth/register`
2. Login with `/api/auth/login` to get a token
3. Include the token in the Authorization header: `Authorization: Bearer <token>`

## Database Integration

The API uses Prisma ORM to interact with the PostgreSQL database. The database schema is defined in the Prisma schema file located at `/prisma/schema.prisma`.

## Security

- Row-Level Security (RLS) policies for data isolation
- JWT token authentication
- Password hashing with bcrypt
- Role-based access control

## AI Features

The API includes AI-powered features that can be enabled/disabled via environment variables:

- Content search using vector embeddings
- AI tutoring for answering student questions
- Automated quiz generation
- Content explanations

Set `ENABLE_AI_FEATURES=true` in your `.env` file to enable these features.
