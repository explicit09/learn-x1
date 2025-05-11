-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add vector column to content_chunks table
ALTER TABLE content_chunks ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index for similarity search
CREATE INDEX IF NOT EXISTS content_chunks_embedding_idx ON content_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- Function to update embeddings
CREATE OR REPLACE FUNCTION update_content_chunk_embedding()
RETURNS TRIGGER AS $$
BEGIN
    -- This is a placeholder. In a real implementation, you would call your embedding service here
    -- or handle this in your application code.
    -- NEW.embedding = ...
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update embeddings when content is updated
DROP TRIGGER IF EXISTS update_content_chunk_embedding_trigger ON content_chunks;
CREATE TRIGGER update_content_chunk_embedding_trigger
BEFORE INSERT OR UPDATE OF content ON content_chunks
FOR EACH ROW
EXECUTE FUNCTION update_content_chunk_embedding();

-- Add similarity search functions
CREATE OR REPLACE FUNCTION search_content_chunks(query_embedding vector, similarity_threshold float, match_count int)
RETURNS TABLE (
    id uuid,
    content text,
    material_id uuid,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id::uuid,
        c.content,
        c.material_id::uuid,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM
        content_chunks c
    WHERE
        c.embedding IS NOT NULL
        AND 1 - (c.embedding <=> query_embedding) > similarity_threshold
    ORDER BY
        c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
