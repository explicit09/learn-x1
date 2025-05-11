# Vector Database Configuration

## Overview

The LEARN-X platform uses PostgreSQL with the pgvector extension to store and query vector embeddings for AI-powered content retrieval. This document describes the vector database configuration, services, and usage patterns.

## Components

### 1. Vector Database Service

The `VectorDatabaseService` handles low-level interactions with the pgvector extension and provides methods for generating and storing embeddings, as well as performing similarity searches.

**Key Features:**
- Ensures pgvector extension is enabled in the database
- Creates and manages vector indexes for efficient similarity search
- Generates and stores embeddings for content chunks
- Performs similarity searches using vector operations

**Key Methods:**
- `ensure_pgvector_extension()` - Ensures the pgvector extension is enabled
- `create_vector_index()` - Creates vector indexes for efficient similarity search
- `generate_and_store_embeddings()` - Generates and stores embeddings for content
- `batch_generate_embeddings()` - Processes multiple content chunks in batch
- `similarity_search()` - Performs similarity search using vector operations

### 2. Content Chunking Service

The `ContentChunkingService` handles breaking down materials into smaller chunks suitable for embedding generation and retrieval.

**Key Features:**
- Splits content into chunks of appropriate size for embedding
- Maintains context through chunk overlap
- Finds natural break points in text (paragraphs, sentences, etc.)
- Stores chunks in the database for later embedding generation

**Key Methods:**
- `chunk_text()` - Splits text into chunks of appropriate size
- `chunk_material()` - Processes a material into content chunks
- `process_all_materials()` - Processes all materials that don't have chunks yet

### 3. Vector Search Service

The `VectorSearchService` provides high-level search and retrieval functionality using vector embeddings.

**Key Features:**
- Semantic search using vector similarity
- Context retrieval for AI-powered question answering
- Related material discovery based on semantic similarity

**Key Methods:**
- `search_by_query()` - Searches for content similar to a query
- `get_relevant_context()` - Retrieves context for a query
- `answer_with_context()` - Answers questions using retrieved context
- `find_related_materials()` - Finds materials related to a query

## Database Schema

### Content Chunks Table

The `content_chunks` table stores content chunks with vector embeddings:

```sql
CREATE TABLE content_chunks (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    material_id UUID NOT NULL REFERENCES materials(id),
    embedding VECTOR(1536),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Vector Index

An IVFFlat index is created for efficient similarity search:

```sql
CREATE INDEX content_chunks_embedding_idx 
ON content_chunks USING ivfflat (embedding vector_l2_ops) 
WITH (lists = 100);
```

### Search Function

A SQL function is created for similarity search:

```sql
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
```

## Setup and Configuration

### 1. Enabling pgvector Extension

The pgvector extension must be enabled in the PostgreSQL database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

This is handled automatically by the `apply_vector_migration.py` script and the `VectorDatabaseService.ensure_pgvector_extension()` method.

### 2. Creating Vector Indexes

Vector indexes are created for efficient similarity search:

```sql
CREATE INDEX content_chunks_embedding_idx 
ON content_chunks USING ivfflat (embedding vector_l2_ops) 
WITH (lists = 100);
```

This is handled automatically by the `apply_vector_migration.py` script and the `VectorDatabaseService.create_vector_index()` method.

### 3. Processing Materials

Materials are processed into content chunks using the `process_materials.py` script:

```bash
python scripts/process_materials.py
```

To process a specific material:

```bash
python scripts/process_materials.py <material_id>
```

### 4. Generating Embeddings

Embeddings are generated for content chunks using the `generate_embeddings.py` script:

```bash
python scripts/generate_embeddings.py process
```

To process a specific material's embeddings:

```bash
python scripts/generate_embeddings.py material <material_id>
```

To test similarity search:

```bash
python scripts/generate_embeddings.py search "your search query"
```

## API Endpoints

The vector search functionality is exposed through the following API endpoints:

### 1. Search Content

```
GET /api/vector-search/search?query=<query>&similarity_threshold=0.7&match_count=5
```

Searches for content similar to the query using vector similarity.

### 2. Answer Question

```
GET /api/vector-search/answer?question=<question>&max_context_chunks=3
```

Answers a question using relevant context from vector search.

### 3. Find Related Materials

```
GET /api/vector-search/related-materials?query=<query>&max_materials=5
```

Finds materials related to a query based on vector similarity.

### 4. Process Material Embeddings

```
POST /api/vector-search/process-material/{material_id}
```

Processes a material's content chunks for embeddings.

## Usage Examples

### 1. Searching for Content

```python
# Using the VectorSearchService
results = await vector_search_service.search_by_query(
    query="machine learning algorithms",
    similarity_threshold=0.7,
    match_count=5
)

# Using the API
import requests

response = requests.get(
    "http://localhost:8000/api/vector-search/search",
    params={
        "query": "machine learning algorithms",
        "similarity_threshold": 0.7,
        "match_count": 5
    },
    headers={"Authorization": f"Bearer {token}"}
)

results = response.json()
```

### 2. Answering Questions with Context

```python
# Using the VectorSearchService
result = await vector_search_service.answer_with_context(
    question="What are the main types of machine learning algorithms?",
    max_context_chunks=3
)

# Using the API
import requests

response = requests.get(
    "http://localhost:8000/api/vector-search/answer",
    params={
        "question": "What are the main types of machine learning algorithms?",
        "max_context_chunks": 3
    },
    headers={"Authorization": f"Bearer {token}"}
)

result = response.json()
```

### 3. Finding Related Materials

```python
# Using the VectorSearchService
materials = await vector_search_service.find_related_materials(
    query="neural networks",
    max_materials=5
)

# Using the API
import requests

response = requests.get(
    "http://localhost:8000/api/vector-search/related-materials",
    params={
        "query": "neural networks",
        "max_materials": 5
    },
    headers={"Authorization": f"Bearer {token}"}
)

materials = response.json()
```

## Performance Considerations

### 1. Index Types

The pgvector extension supports different index types:

- **IVFFlat**: Good balance of search speed and accuracy
- **HNSW**: Faster search but slower index creation

We're using IVFFlat with 100 lists, which is a good default for most use cases.

### 2. Embedding Dimension

We're using OpenAI's embedding model, which has 1536 dimensions. If you switch to a different embedding model, you'll need to update the vector dimension in the database schema.

### 3. Batch Processing

Embedding generation is computationally expensive, so we use batch processing to generate embeddings for multiple content chunks at once.

## Maintenance Tasks

### 1. Reindexing

If you add a large number of new content chunks, you may need to reindex the vector index:

```sql
REINDEX INDEX content_chunks_embedding_idx;
```

### 2. Updating Embeddings

If you update the content of a chunk, you'll need to regenerate its embedding:

```python
await vector_database_service.generate_and_store_embeddings(
    content_chunk_id="chunk_id",
    content="Updated content"
)
```

### 3. Monitoring Index Size

Vector indexes can become large. Monitor the size of the index using:

```sql
SELECT pg_size_pretty(pg_relation_size('content_chunks_embedding_idx'));
```

## Troubleshooting

### 1. Slow Similarity Searches

If similarity searches are slow, try:

- Increasing the number of lists in the IVFFlat index
- Switching to an HNSW index
- Adding more RAM to the database server

### 2. Missing Embeddings

If content chunks are missing embeddings, run:

```bash
python scripts/generate_embeddings.py process
```

### 3. pgvector Extension Issues

If you encounter issues with the pgvector extension, ensure it's properly installed and enabled:

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## Future Enhancements

1. **Hybrid Search**: Combine vector search with keyword search for better results
2. **Chunking Improvements**: More sophisticated content chunking strategies
3. **Embedding Caching**: Cache embeddings to reduce API calls
4. **Automatic Reindexing**: Periodically reindex the vector index
5. **Alternative Embedding Models**: Support for different embedding models
