# LEARN-X System Architecture

## Overview

LEARN-X follows a modular, microservice-oriented architecture designed for scalability, maintainability, and performance. The system is built with an AI-first approach, ensuring that artificial intelligence is not just a feature but a core component of the platform.

## Core Principles

- **Modularity**: Components are isolated for independent development and scaling
- **AI-Native**: AI capabilities are integrated at the foundation, not as an afterthought
- **Security-First**: Multi-tenant isolation and data protection at every layer
- **Scalability**: Asynchronous processing and horizontal scaling for growth
- **Maintainability**: Clean code organization and comprehensive documentation

## System Components

### 1. Frontend Application

#### Technology Stack
- **Framework**: Next.js (App Router)
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **Authentication**: Clerk/Supabase Auth

#### Key Components
- **Authentication Pages**: Login, registration, and account management
- **Student Dashboard**: Course overview, progress tracking, and learning metrics
- **Learning Interface**: AI tutor interaction and content delivery
- **Quiz System**: Interactive quiz taking and review
- **Professor Dashboard**: Course management, student analytics, and AI review

#### Structure
```
apps/frontend/
├── public/
├── src/
│   ├── app/            # App Router pages and layouts
│   ├── components/     # Reusable UI components
│   ├── lib/            # Utility functions and API clients
│   ├── hooks/          # Custom React hooks
│   └── styles/         # Global styles
├── tailwind.config.js
└── next.config.js
```

### 2. API Service

#### Technology Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector
- **ORM**: SQLAlchemy/Prisma
- **Authentication**: JWT with OAuth2

#### Key Endpoints
- **/api/auth/**: Authentication and session management
- **/api/student/**: Student-specific operations
- **/api/professor/**: Professor-specific operations
- **/api/courses/**: Course management and content
- **/api/quizzes/**: Quiz generation and submission
- **/api/files/**: File upload and management

#### Structure
```
apps/api/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── student.py
│   │   │   ├── professor.py
│   │   │   ├── courses.py
│   │   │   ├── quizzes.py
│   │   │   └── files.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── middleware.py
│   ├── db/
│   │   ├── models/
│   │   ├── crud/
│   │   └── session.py
│   ├── schemas/
│   ├── services/
│   └── main.py
└── Dockerfile
```

### 3. AI Microservices

#### Technology Stack
- **Framework**: FastAPI (Python)
- **AI/ML**: LangChain, OpenAI API, SentenceTransformers
- **Vector Store**: pgvector (PostgreSQL)

#### Key Services
- **Upload Parser**: Processes PDFs, documents, and audio files
- **Embedder**: Generates vector embeddings for content
- **Tutor Agent**: Manages AI tutoring interactions
- **Quiz Generator**: Creates personalized quizzes

#### Structure
```
apps/ai/
├── upload_parser/
│   ├── main.py
│   ├── parser.py
│   └── utils/
├── embedder/
│   ├── main.py
│   ├── embed.py
│   └── model_loader.py
├── tutor_agent/
│   ├── main.py
│   ├── chains/
│   ├── memory/
│   └── prompts/
├── quiz_generator/
│   ├── main.py
│   └── templates/
└── Dockerfile
```

### 4. Worker Service

#### Technology Stack
- **Task Queue**: Celery
- **Message Broker**: Redis
- **Storage**: S3-compatible (Cloudflare R2)

#### Key Tasks
- **File Processing**: Converting uploads to text and embeddings
- **Batch Analytics**: Processing usage data for insights
- **Scheduled Tasks**: Maintenance and cleanup operations

#### Structure
```
workers/celery/
├── tasks/
│   ├── file_processing.py
│   ├── analytics.py
│   └── maintenance.py
├── celeryconfig.py
└── main.py
```

### 5. Database Architecture

#### Primary Database: PostgreSQL

##### Core Schemas
- **auth**: User accounts, roles, and permissions
- **content**: Courses, materials, and content metadata
- **learning**: Student progress, quiz results, and interactions
- **analytics**: Usage data, performance metrics, and insights

##### Key Tables
- **users**: Core user data and authentication details
- **organizations**: Educational institutions and tenant information
- **courses**: Course information and structure
- **materials**: Uploaded content and metadata
- **vectors**: Content embeddings for AI retrieval
- **interactions**: Student-AI interactions and feedback
- **quiz_items**: Quiz questions and answers
- **quiz_results**: Student quiz performance

#### Security Implementation
- Row-Level Security (RLS) policies for multi-tenant isolation
- Organization and course-level access controls
- Encrypted sensitive data fields

### 6. Infrastructure

#### Development Environment
- Docker Compose for local development
- Local S3-compatible storage (MinIO)
- Development database with sample data

#### Production Environment
- Containerized services on Kubernetes or managed platforms
- Cloudflare R2 or AWS S3 for file storage
- Managed PostgreSQL with pgvector extension
- Redis for caching and message brokering

#### CI/CD Pipeline
- GitHub Actions for automated testing and deployment
- Staging and production environments
- Automated database migrations

## Data Flows

### Student Learning Flow
1. Student logs in via frontend authentication
2. Student selects a course and accesses learning materials
3. Student uploads additional materials (e.g., lecture notes)
4. Upload is processed by the worker service:
   - File is stored in S3
   - Text is extracted and processed
   - Embeddings are generated and stored
5. Student asks a question to the AI tutor
6. Question is routed to the tutor agent service:
   - Context is retrieved using vector search
   - LangChain processes the question with context
   - Personalized response is generated
7. Response is returned to the student and stored for future reference
8. Student provides feedback on the response quality
9. Analytics are updated to track engagement and effectiveness

### Professor Insight Flow
1. Professor logs in via frontend authentication
2. Professor accesses the course dashboard
3. System aggregates student interactions and questions
4. Confusion heatmap is generated showing problem areas
5. Professor reviews AI responses for accuracy
6. Professor uploads additional materials to address gaps
7. Analytics provide insights on course effectiveness

## Security Architecture

### Authentication and Authorization
- JWT-based authentication with secure token handling
- OAuth2 integration for SSO with educational institutions
- Role-based access control (RBAC) for feature access
- Organization-level permissions for multi-tenant isolation

### Data Protection
- PostgreSQL Row-Level Security for data isolation
- Encrypted data at rest and in transit
- Signed URLs for temporary file access
- FERPA-compliant data handling for educational information

### API Security
- Rate limiting to prevent abuse
- Input validation and sanitization
- CSRF protection for web endpoints
- Comprehensive logging and monitoring

## Scalability Considerations

### Horizontal Scaling
- Stateless API services for easy replication
- Database connection pooling and optimization
- Caching strategies for frequently accessed data

### Performance Optimization
- Asynchronous processing for heavy operations
- Efficient vector search algorithms
- Optimized database queries and indexes

### Resource Management
- Auto-scaling based on load metrics
- Resource limits for AI operations
- Tiered storage for hot and cold data

## Monitoring and Observability

### Logging
- Structured logging for all services
- Centralized log collection and analysis
- Error tracking and alerting

### Metrics
- Performance metrics for API endpoints
- Resource utilization monitoring
- User engagement and activity tracking

### Alerting
- Automated alerts for system issues
- Performance degradation detection
- Security incident notifications

## Future Extensibility

### Integration Points
- LMS integration via LTI 1.3 or API connectors
- Additional AI model support
- External analytics and reporting tools

### Planned Enhancements
- Real-time collaboration features
- Advanced personalization algorithms
- Mobile application support
- Expanded content format support
