-- Enable Row Level Security
ALTER TABLE "organizations" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "learning_styles" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "courses" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "enrollments" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "modules" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "topics" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "materials" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "content_chunks" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "quizzes" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "questions" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "question_options" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "quiz_attempts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "question_answers" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "ai_interactions" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "analytics_events" ENABLE ROW LEVEL SECURITY;

-- Create function to set current user context
CREATE OR REPLACE FUNCTION set_current_user_id(user_id text)
RETURNS void AS $$
BEGIN
  PERFORM set_config('app.current_user_id', user_id, false);
END;
$$ LANGUAGE plpgsql;

-- Create RLS Policies for organizations
CREATE POLICY "organizations_isolation_policy" ON "organizations"
    USING (id IN (
        SELECT "organizationId" FROM "users"
        WHERE "users".id = current_setting('app.current_user_id', true)
    ));

-- Create RLS Policies for users
CREATE POLICY "users_isolation_policy" ON "users"
    USING ("organizationId" = (
        SELECT "organizationId" FROM "users"
        WHERE "users".id = current_setting('app.current_user_id', true)
    ));

-- Create RLS Policies for courses
CREATE POLICY "courses_isolation_policy" ON "courses"
    USING ("organizationId" = (
        SELECT "organizationId" FROM "users"
        WHERE "users".id = current_setting('app.current_user_id', true)
    ));

-- Create RLS Policies for enrollments
CREATE POLICY "enrollments_isolation_policy" ON "enrollments"
    USING ("userId" = current_setting('app.current_user_id', true) OR
           "courseId" IN (
               SELECT "id" FROM "courses"
               WHERE "professorId" = current_setting('app.current_user_id', true)
           ));

-- Create RLS Policies for modules
CREATE POLICY "modules_isolation_policy" ON "modules"
    USING ("courseId" IN (
        SELECT "id" FROM "courses"
        WHERE "organizationId" = (
            SELECT "organizationId" FROM "users"
            WHERE "users".id = current_setting('app.current_user_id', true)
        )
    ));

-- Create RLS Policies for topics
CREATE POLICY "topics_isolation_policy" ON "topics"
    USING ("moduleId" IN (
        SELECT "id" FROM "modules"
        WHERE "courseId" IN (
            SELECT "id" FROM "courses"
            WHERE "organizationId" = (
                SELECT "organizationId" FROM "users"
                WHERE "users".id = current_setting('app.current_user_id', true)
            )
        )
    ));

-- Create RLS Policies for materials
CREATE POLICY "materials_isolation_policy" ON "materials"
    USING ("topicId" IN (
        SELECT "id" FROM "topics"
        WHERE "moduleId" IN (
            SELECT "id" FROM "modules"
            WHERE "courseId" IN (
                SELECT "id" FROM "courses"
                WHERE "organizationId" = (
                    SELECT "organizationId" FROM "users"
                    WHERE "users".id = current_setting('app.current_user_id', true)
                )
            )
        )
    ));

-- Create RLS Policies for content_chunks
CREATE POLICY "content_chunks_isolation_policy" ON "content_chunks"
    USING ("materialId" IN (
        SELECT "id" FROM "materials"
        WHERE "topicId" IN (
            SELECT "id" FROM "topics"
            WHERE "moduleId" IN (
                SELECT "id" FROM "modules"
                WHERE "courseId" IN (
                    SELECT "id" FROM "courses"
                    WHERE "organizationId" = (
                        SELECT "organizationId" FROM "users"
                        WHERE "users".id = current_setting('app.current_user_id', true)
                    )
                )
            )
        )
    ));

-- Create RLS Policies for quizzes
CREATE POLICY "quizzes_isolation_policy" ON "quizzes"
    USING ("courseId" IN (
        SELECT "id" FROM "courses"
        WHERE "organizationId" = (
            SELECT "organizationId" FROM "users"
            WHERE "users".id = current_setting('app.current_user_id', true)
        )
    ));

-- Create RLS Policies for questions
CREATE POLICY "questions_isolation_policy" ON "questions"
    USING ("quizId" IN (
        SELECT "id" FROM "quizzes"
        WHERE "courseId" IN (
            SELECT "id" FROM "courses"
            WHERE "organizationId" = (
                SELECT "organizationId" FROM "users"
                WHERE "users".id = current_setting('app.current_user_id', true)
            )
        )
    ));

-- Create RLS Policies for question_options
CREATE POLICY "question_options_isolation_policy" ON "question_options"
    USING ("questionId" IN (
        SELECT "id" FROM "questions"
        WHERE "quizId" IN (
            SELECT "id" FROM "quizzes"
            WHERE "courseId" IN (
                SELECT "id" FROM "courses"
                WHERE "organizationId" = (
                    SELECT "organizationId" FROM "users"
                    WHERE "users".id = current_setting('app.current_user_id', true)
                )
            )
        )
    ));

-- Create RLS Policies for quiz_attempts
CREATE POLICY "quiz_attempts_isolation_policy" ON "quiz_attempts"
    USING ("userId" = current_setting('app.current_user_id', true) OR
           "quizId" IN (
               SELECT "id" FROM "quizzes"
               WHERE "courseId" IN (
                   SELECT "id" FROM "courses"
                   WHERE "professorId" = current_setting('app.current_user_id', true)
               )
           ));

-- Create RLS Policies for question_answers
CREATE POLICY "question_answers_isolation_policy" ON "question_answers"
    USING ("quizAttemptId" IN (
        SELECT "id" FROM "quiz_attempts"
        WHERE "userId" = current_setting('app.current_user_id', true) OR
              "quizId" IN (
                  SELECT "id" FROM "quizzes"
                  WHERE "courseId" IN (
                      SELECT "id" FROM "courses"
                      WHERE "professorId" = current_setting('app.current_user_id', true)
                  )
              )
    ));

-- Create RLS Policies for ai_interactions
CREATE POLICY "ai_interactions_isolation_policy" ON "ai_interactions"
    USING ("userId" = current_setting('app.current_user_id', true));

-- Create RLS Policies for analytics_events
CREATE POLICY "analytics_events_isolation_policy" ON "analytics_events"
    USING ("userId" = current_setting('app.current_user_id', true) OR
           "courseId" IN (
               SELECT "id" FROM "courses"
               WHERE "professorId" = current_setting('app.current_user_id', true)
           ));
