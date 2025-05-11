# Database Implementation for LEARN-X

## Overview

This directory contains the Prisma ORM setup for the LEARN-X platform's database implementation. The database is designed according to the requirements in the PRD, featuring a multi-tenant architecture with organization-level isolation, role-based access control, and Row-Level Security (RLS) policies for data protection.

## Schema Design

The database schema implements the following key components:

- **Multi-tenant Architecture**: Organization-level isolation with Row-Level Security
- **User Management**: Role-based access control (student, professor, admin)
- **Course Management**: Courses, modules, topics, and materials
- **Content Storage**: Material content with vector embeddings for AI retrieval
- **Quiz System**: Quizzes, questions, and student attempts with spaced repetition
- **AI Tutoring**: Interaction tracking and personalization
- **Analytics**: Event logging and learning outcome measurements

## Security Features

- **Row-Level Security**: PostgreSQL RLS policies for data isolation
- **Role-Based Access**: Different access levels based on user roles
- **Secure Context**: User context tracking for policy enforcement

## Getting Started

### Prerequisites

- PostgreSQL 14+ with pgvector extension
- Node.js 18+
- Prisma CLI

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Configure the `DATABASE_URL` variable

3. Generate Prisma client:
   ```bash
   npx prisma generate
   ```

4. Run migrations:
   ```bash
   npx prisma migrate dev
   ```

## Database Schema

The schema includes the following main entities:

- **Organization**: Multi-tenant isolation
- **User**: Role-based access control
- **Course**: Educational content organization
- **Module/Topic**: Content hierarchy
- **Material**: Educational materials with file storage
- **ContentChunk**: Vector embeddings for AI retrieval
- **Quiz/Question**: Interactive assessment system
- **AIInteraction**: Tutoring system tracking
- **AnalyticsEvent**: Event logging for insights

## Row-Level Security

The database implements PostgreSQL Row-Level Security (RLS) policies to ensure data isolation between organizations and appropriate access controls within organizations. These policies are automatically applied during migration.

## Vector Support

The database uses the pgvector extension to store and query vector embeddings for AI-powered content retrieval and personalization features.

## Testing

To run database tests:

```bash
npm run test:db
```

## Migrations

### Creating a new migration

```bash
npx prisma migrate dev --name migration_name
```

### Applying migrations in production

```bash
npx prisma migrate deploy
```
