import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import numpy as np
from app.services.embeddings import EmbeddingsService
from app.services.openai import OpenAIService
from app.services.text_chunking import TextChunkingService

@pytest.fixture
def mock_openai_service():
    with patch('app.services.embeddings.openai_service') as mock:
        mock.generate_embedding = AsyncMock()
        yield mock

@pytest.fixture
def mock_text_chunking_service():
    with patch('app.services.embeddings.text_chunking_service') as mock:
        mock.chunk_text = MagicMock()
        yield mock

@pytest.fixture
def mock_prisma():
    with patch('app.services.embeddings.prisma') as mock:
        # Mock ContentChunk model
        mock.contentchunk.find_many = AsyncMock()
        mock.contentchunk.create = AsyncMock()
        mock.contentchunk.update = AsyncMock()
        mock.contentchunk.delete = AsyncMock()
        
        # Mock Material model
        mock.material.find_unique = AsyncMock()
        mock.material.find_many = AsyncMock()
        
        # Mock raw queries
        mock.query_raw = AsyncMock()
        
        yield mock

@pytest.fixture
def embeddings_service():
    return EmbeddingsService()

@pytest.mark.asyncio
async def test_generate_embeddings_for_material(embeddings_service, mock_openai_service, mock_text_chunking_service, mock_prisma):
    # Setup test data
    material_id = "material123"
    organization_id = "org123"
    content = "This is a test material content. It contains information about various topics."
    
    # Mock material data
    mock_material = MagicMock(
        id=material_id,
        content=content,
        organization_id=organization_id
    )
    mock_prisma.material.find_unique.return_value = mock_material
    
    # Mock text chunking
    chunks = ["This is a test material content.", "It contains information about various topics."]
    mock_text_chunking_service.chunk_text.return_value = chunks
    
    # Mock embedding generation
    mock_embeddings = [
        {"embedding": [0.1, 0.2, 0.3], "tokens_used": 5},
        {"embedding": [0.4, 0.5, 0.6], "tokens_used": 6}
    ]
    mock_openai_service.generate_embedding.side_effect = mock_embeddings
    
    # Mock content chunk creation
    mock_content_chunks = [
        MagicMock(id="chunk1", content=chunks[0], materialId=material_id),
        MagicMock(id="chunk2", content=chunks[1], materialId=material_id)
    ]
    mock_prisma.contentchunk.create.side_effect = mock_content_chunks
    
    # Call the method
    result = await embeddings_service.generate_embeddings_for_material(material_id)
    
    # Verify the result
    assert result["material_id"] == material_id
    assert result["chunks_processed"] == 2
    assert result["total_tokens"] == 11  # 5 + 6
    
    # Verify material was retrieved
    mock_prisma.material.find_unique.assert_called_once_with(
        where={"id": material_id}
    )
    
    # Verify text was chunked
    mock_text_chunking_service.chunk_text.assert_called_once_with(content)
    
    # Verify embeddings were generated
    assert mock_openai_service.generate_embedding.call_count == 2
    
    # Verify content chunks were created
    assert mock_prisma.contentchunk.create.call_count == 2
    for i, call_args in enumerate(mock_prisma.contentchunk.create.call_args_list):
        data = call_args[1]["data"]
        assert data["content"] == chunks[i]
        assert data["materialId"] == material_id
        assert "embedding" in data

@pytest.mark.asyncio
async def test_generate_embeddings_material_not_found(embeddings_service, mock_prisma):
    # Mock material not found
    mock_prisma.material.find_unique.return_value = None
    
    # Call the method and expect an exception
    with pytest.raises(ValueError) as excinfo:
        await embeddings_service.generate_embeddings_for_material("nonexistent")
    
    # Verify the error message
    assert "Material not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_search_similar_content(embeddings_service, mock_openai_service, mock_prisma):
    # Setup test data
    query = "What is photosynthesis?"
    material_ids = ["material1", "material2"]
    limit = 5
    similarity_threshold = 0.7
    
    # Mock embedding generation for query
    query_embedding = {"embedding": [0.1, 0.2, 0.3], "tokens_used": 5}
    mock_openai_service.generate_embedding.return_value = query_embedding
    
    # Mock similar content results
    mock_results = [
        {
            "id": "chunk1",
            "content": "Photosynthesis is the process used by plants to convert light energy into chemical energy.",
            "material_id": "material1",
            "similarity": 0.92,
            "material_title": "Biology 101"
        },
        {
            "id": "chunk2",
            "content": "During photosynthesis, plants take in carbon dioxide and water to produce glucose and oxygen.",
            "similarity": 0.85,
            "material_id": "material1",
            "material_title": "Biology 101"
        },
        {
            "id": "chunk3",
            "content": "The light reactions of photosynthesis occur in the thylakoid membrane of the chloroplast.",
            "similarity": 0.78,
            "material_id": "material2",
            "material_title": "Advanced Biology"
        }
    ]
    mock_prisma.query_raw.return_value = mock_results
    
    # Call the method
    result = await embeddings_service.search_similar_content(
        query=query,
        material_ids=material_ids,
        limit=limit,
        similarity_threshold=similarity_threshold
    )
    
    # Verify the result
    assert len(result) == 3
    assert result[0]["content"] == "Photosynthesis is the process used by plants to convert light energy into chemical energy."
    assert result[0]["similarity"] == 0.92
    assert result[0]["material_id"] == "material1"
    assert result[0]["material_title"] == "Biology 101"
    
    # Verify embedding was generated for query
    mock_openai_service.generate_embedding.assert_called_once_with(query)
    
    # Verify raw query was executed
    mock_prisma.query_raw.assert_called_once()
    # The query should include the material_ids and similarity_threshold
    query_args = mock_prisma.query_raw.call_args[0][1]
    assert query_embedding["embedding"] in query_args
    assert similarity_threshold in query_args
    assert limit in query_args

@pytest.mark.asyncio
async def test_search_similar_content_no_results(embeddings_service, mock_openai_service, mock_prisma):
    # Setup test data
    query = "What is quantum physics?"
    
    # Mock embedding generation for query
    query_embedding = {"embedding": [0.1, 0.2, 0.3], "tokens_used": 5}
    mock_openai_service.generate_embedding.return_value = query_embedding
    
    # Mock empty results
    mock_prisma.query_raw.return_value = []
    
    # Call the method
    result = await embeddings_service.search_similar_content(query=query)
    
    # Verify the result is empty
    assert len(result) == 0

@pytest.mark.asyncio
async def test_delete_embeddings_for_material(embeddings_service, mock_prisma):
    # Setup test data
    material_id = "material123"
    
    # Mock content chunks
    mock_chunks = [
        MagicMock(id="chunk1"),
        MagicMock(id="chunk2")
    ]
    mock_prisma.contentchunk.find_many.return_value = mock_chunks
    
    # Call the method
    result = await embeddings_service.delete_embeddings_for_material(material_id)
    
    # Verify the result
    assert result["material_id"] == material_id
    assert result["chunks_deleted"] == 2
    
    # Verify chunks were retrieved
    mock_prisma.contentchunk.find_many.assert_called_once_with(
        where={"materialId": material_id}
    )
    
    # Verify each chunk was deleted
    assert mock_prisma.contentchunk.delete.call_count == 2
    for i, chunk in enumerate(mock_chunks):
        mock_prisma.contentchunk.delete.assert_any_call(
            where={"id": chunk.id}
        )

@pytest.mark.asyncio
async def test_update_embeddings_for_material(embeddings_service, mock_prisma):
    # Setup test data
    material_id = "material123"
    
    # Mock the delete and generate methods
    with patch.object(embeddings_service, 'delete_embeddings_for_material', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = {"material_id": material_id, "chunks_deleted": 2}
        
        with patch.object(embeddings_service, 'generate_embeddings_for_material', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "material_id": material_id,
                "chunks_processed": 3,
                "total_tokens": 15
            }
            
            # Call the method
            result = await embeddings_service.update_embeddings_for_material(material_id)
            
            # Verify the result
            assert result["material_id"] == material_id
            assert result["old_chunks_deleted"] == 2
            assert result["new_chunks_processed"] == 3
            assert result["total_tokens"] == 15
            
            # Verify delete and generate were called
            mock_delete.assert_called_once_with(material_id)
            mock_generate.assert_called_once_with(material_id)
