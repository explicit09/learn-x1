# LEARN-X Database Schema

## Overview

This document outlines the database schema for the LEARN-X platform. The schema is designed to support multi-tenant isolation, personalized learning experiences, and comprehensive analytics while maintaining security and performance.

## Schema Design Principles

- **Multi-tenant Isolation**: Organization-level separation of data
- **Role-Based Access**: Different schemas for different user types
- **Vector Support**: Efficient storage and retrieval of embeddings
- **Performance**: Optimized indexes and query patterns
- **Security**: Row-level security policies for data protection

## Core Tables

### Organizations

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_org_isolation ON users
    USING (organization_id = current_setting('app.current_org_id')::UUID);
```

### User Preferences

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    learning_style VARCHAR(50),
    interests JSONB,
    ui_preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_preferences_isolation ON user_preferences
    USING (user_id IN (SELECT id FROM users WHERE organization_id = current_setting('app.current_org_id')::UUID));
```

### Courses

```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    created_by UUID NOT NULL REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

CREATE POLICY courses_org_isolation ON courses
    USING (organization_id = current_setting('app.current_org_id')::UUID);
```

### Course Enrollments

```sql
CREATE TABLE course_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(course_id, user_id)
);

-- Row-Level Security Policy
ALTER TABLE course_enrollments ENABLE ROW LEVEL SECURITY;

CREATE POLICY enrollments_org_isolation ON course_enrollments
    USING (course_id IN (SELECT id FROM courses WHERE organization_id = current_setting('app.current_org_id')::UUID));
```

### Materials

```sql
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    course_id UUID NOT NULL REFERENCES courses(id),
    uploaded_by UUID NOT NULL REFERENCES users(id),
    file_path VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

CREATE POLICY materials_org_isolation ON materials
    USING (course_id IN (SELECT id FROM courses WHERE organization_id = current_setting('app.current_org_id')::UUID));
```

### Material Content

```sql
CREATE TABLE material_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES materials(id),
    content_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE material_content ENABLE ROW LEVEL SECURITY;

CREATE POLICY content_org_isolation ON material_content
    USING (material_id IN (SELECT id FROM materials WHERE course_id IN 
                          (SELECT id FROM courses WHERE organization_id = current_setting('app.current_org_id')::UUID)));
```

### Vector Embeddings

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_content_id UUID NOT NULL REFERENCES material_content(id),
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Row-Level Security Policy
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY embeddings_org_isolation ON embeddings
    USING (material_content_id IN (SELECT id FROM material_content WHERE material_id IN 
                                  (SELECT id FROM materials WHERE course_id IN 
                                  (SELECT id FROM courses WHERE organization_id = current_setting('app.current_org_id')::UUID))));
```

### AI Interactions

```sql
CREATE TABLE ai_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    relevant_material_ids UUID[] NOT NULL,
    feedback_rating INTEGER,
    feedback_comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE ai_interactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY interactions_user_isolation ON ai_interactions
    USING (user_id = current_setting('app.current_user_id')::UUID OR 
           course_id IN (SELECT course_id FROM course_enrollments WHERE user_id = current_setting('app.current_user_id')::UUID AND role = 'professor'));
```

### Quizzes

```sql
CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    course_id UUID NOT NULL REFERENCES courses(id),
    created_by UUID NOT NULL REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE quizzes ENABLE ROW LEVEL SECURITY;

CREATE POLICY quizzes_org_isolation ON quizzes
    USING (course_id IN (SELECT id FROM courses WHERE organization_id = current_setting('app.current_org_id')::UUID));
```

### Quiz Questions

```sql
CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id),
    question TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    options JSONB,
    correct_answer TEXT,
    explanation TEXT,
    points INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY questions_org_isolation ON quiz_questions
    USING (quiz_id IN (SELECT id FROM quizzes WHERE course_id IN 
                      (SELECT id FROM courses WHERE organization_id = current_setting('app.current_org_id')::UUID)));
```

### Quiz Attempts

```sql
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id),
    user_id UUID NOT NULL REFERENCES users(id),
    score INTEGER,
    max_score INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;

CREATE POLICY attempts_user_isolation ON quiz_attempts
    USING (user_id = current_setting('app.current_user_id')::UUID OR 
           quiz_id IN (SELECT id FROM quizzes WHERE course_id IN 
                      (SELECT course_id FROM course_enrollments WHERE user_id = current_setting('app.current_user_id')::UUID AND role = 'professor')));
```

### Quiz Responses

```sql
CREATE TABLE quiz_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_attempt_id UUID NOT NULL REFERENCES quiz_attempts(id),
    question_id UUID NOT NULL REFERENCES quiz_questions(id),
    user_answer TEXT,
    is_correct BOOLEAN,
    points_earned INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE quiz_responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY responses_user_isolation ON quiz_responses
    USING (quiz_attempt_id IN (SELECT id FROM quiz_attempts WHERE user_id = current_setting('app.current_user_id')::UUID OR 
                              quiz_id IN (SELECT id FROM quizzes WHERE course_id IN 
                                         (SELECT course_id FROM course_enrollments WHERE user_id = current_setting('app.current_user_id')::UUID AND role = 'professor'))));
```

### Analytics

```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row-Level Security Policy
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY analytics_org_isolation ON analytics_events
    USING (organization_id = current_setting('app.current_org_id')::UUID);
```

## Indexes

```sql
-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org_id ON users(organization_id);

-- Course indexes
CREATE INDEX idx_courses_org_id ON courses(organization_id);
CREATE INDEX idx_courses_created_by ON courses(created_by);

-- Enrollment indexes
CREATE INDEX idx_enrollments_course_id ON course_enrollments(course_id);
CREATE INDEX idx_enrollments_user_id ON course_enrollments(user_id);

-- Material indexes
CREATE INDEX idx_materials_course_id ON materials(course_id);
CREATE INDEX idx_materials_uploaded_by ON materials(uploaded_by);

-- AI interaction indexes
CREATE INDEX idx_interactions_user_id ON ai_interactions(user_id);
CREATE INDEX idx_interactions_course_id ON ai_interactions(course_id);
CREATE INDEX idx_interactions_created_at ON ai_interactions(created_at);

-- Quiz indexes
CREATE INDEX idx_quizzes_course_id ON quizzes(course_id);
CREATE INDEX idx_quiz_questions_quiz_id ON quiz_questions(quiz_id);
CREATE INDEX idx_quiz_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX idx_quiz_attempts_quiz_id ON quiz_attempts(quiz_id);
```

## Views

### Professor Insights View

```sql
CREATE OR REPLACE VIEW professor_course_insights AS
SELECT 
    c.id AS course_id,
    c.title AS course_title,
    c.organization_id,
    COUNT(DISTINCT ce.user_id) AS enrolled_students,
    COUNT(DISTINCT ai.id) AS total_ai_interactions,
    COUNT(DISTINCT qa.id) AS total_quiz_attempts,
    AVG(qa.score::float / NULLIF(qa.max_score, 0)) AS avg_quiz_score
FROM courses c
LEFT JOIN course_enrollments ce ON c.id = ce.course_id AND ce.role = 'student'
LEFT JOIN ai_interactions ai ON c.id = ai.course_id
LEFT JOIN quizzes q ON c.id = q.course_id
LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id
GROUP BY c.id, c.title, c.organization_id;

-- Row-Level Security Policy
ALTER VIEW professor_course_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY insights_org_isolation ON professor_course_insights
    USING (organization_id = current_setting('app.current_org_id')::UUID);
```

### Confusion Heatmap View

```sql
CREATE OR REPLACE VIEW confusion_heatmap AS
SELECT 
    m.id AS material_id,
    m.title AS material_title,
    m.course_id,
    c.organization_id,
    COUNT(ai.id) AS question_count,
    AVG(COALESCE(ai.feedback_rating, 0)) AS avg_feedback_rating
FROM materials m
JOIN courses c ON m.course_id = c.id
LEFT JOIN ai_interactions ai ON m.id = ANY(ai.relevant_material_ids)
GROUP BY m.id, m.title, m.course_id, c.organization_id;

-- Row-Level Security Policy
ALTER VIEW confusion_heatmap ENABLE ROW LEVEL SECURITY;

CREATE POLICY heatmap_org_isolation ON confusion_heatmap
    USING (organization_id = current_setting('app.current_org_id')::UUID);
```

## Functions

### Vector Similarity Search

```sql
CREATE OR REPLACE FUNCTION search_material_by_embedding(
    query_embedding vector(1536),
    course_id UUID,
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 5
) RETURNS TABLE (
    material_content_id UUID,
    material_id UUID,
    content TEXT,
    similarity float
) LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mc.id AS material_content_id,
        mc.material_id,
        mc.content,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM 
        embeddings e
    JOIN 
        material_content mc ON e.material_content_id = mc.id
    JOIN 
        materials m ON mc.material_id = m.id
    WHERE 
        m.course_id = search_material_by_embedding.course_id
        AND 1 - (e.embedding <=> query_embedding) > similarity_threshold
    ORDER BY 
        similarity DESC
    LIMIT 
        max_results;
END;
$$;
```

### Spaced Repetition Scheduling

```sql
CREATE OR REPLACE FUNCTION get_spaced_repetition_questions(
    p_user_id UUID,
    p_course_id UUID,
    p_count int DEFAULT 5
) RETURNS TABLE (
    question_id UUID,
    question TEXT,
    question_type VARCHAR(50),
    options JSONB,
    last_seen TIMESTAMP WITH TIME ZONE,
    performance_score float
) LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    current_date TIMESTAMP WITH TIME ZONE := NOW();
BEGIN
    RETURN QUERY
    WITH user_question_history AS (
        SELECT 
            qq.id AS question_id,
            MAX(qr.created_at) AS last_seen,
            AVG(CASE WHEN qr.is_correct THEN 1.0 ELSE 0.0 END) AS performance_score
        FROM 
            quiz_questions qq
        JOIN 
            quizzes q ON qq.quiz_id = q.id
        LEFT JOIN 
            quiz_responses qr ON qq.id = qr.question_id
        LEFT JOIN 
            quiz_attempts qa ON qr.quiz_attempt_id = qa.id AND qa.user_id = p_user_id
        WHERE 
            q.course_id = p_course_id
        GROUP BY 
            qq.id
    )
    SELECT 
        qq.id AS question_id,
        qq.question,
        qq.question_type,
        qq.options,
        uqh.last_seen,
        COALESCE(uqh.performance_score, 0.5) AS performance_score
    FROM 
        quiz_questions qq
    JOIN 
        quizzes q ON qq.quiz_id = q.id
    LEFT JOIN 
        user_question_history uqh ON qq.id = uqh.question_id
    WHERE 
        q.course_id = p_course_id
    ORDER BY 
        -- Prioritize questions never seen
        CASE WHEN uqh.last_seen IS NULL THEN 0 ELSE 1 END,
        -- Then by spaced repetition algorithm (lower score = higher priority)
        CASE 
            WHEN uqh.last_seen IS NULL THEN 0
            ELSE EXTRACT(EPOCH FROM (current_date - uqh.last_seen)) / 
                 (86400 * POWER(2, GREATEST(uqh.performance_score * 5, 1)))
        END DESC
    LIMIT 
        p_count;
END;
$$;
```

## Row-Level Security Setup

```sql
-- Function to set current user and organization context
CREATE OR REPLACE FUNCTION set_user_context(
    user_id UUID,
    org_id UUID
) RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::text, false);
    PERFORM set_config('app.current_org_id', org_id::text, false);
END;
$$ LANGUAGE plpgsql;

-- Reset context function
CREATE OR REPLACE FUNCTION reset_user_context() RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_id', '', false);
    PERFORM set_config('app.current_org_id', '', false);
END;
$$ LANGUAGE plpgsql;
```

## Migration Strategy

The database schema will be managed using migration scripts to ensure consistent deployment across environments. Each migration will include:

1. Forward migration (up) script
2. Rollback (down) script
3. Data migration for existing data (if applicable)

Migrations will be applied automatically during deployment using a migration tool such as Alembic (for Python) or similar.
