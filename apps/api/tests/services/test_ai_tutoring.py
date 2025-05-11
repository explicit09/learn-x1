import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from app.services.ai_tutoring import AITutoringService
from app.services.embeddings import EmbeddingsService
from app.services.openai import OpenAIService
from app.services.learning_styles import LearningStyleService

@pytest.fixture
def mock_embeddings_service():
    with patch('app.services.ai_tutoring.embeddings_service') as mock:
        mock.search_similar_content = AsyncMock()
        yield mock

@pytest.fixture
def mock_openai_service():
    with patch('app.services.ai_tutoring.openai_service') as mock:
        mock.generate_completion = AsyncMock()
        yield mock

@pytest.fixture
def mock_learning_style_service():
    with patch('app.services.ai_tutoring.learning_style_service') as mock:
        mock.get_learning_style_recommendations = AsyncMock()
        yield mock

@pytest.fixture
def ai_tutoring_service():
    return AITutoringService()

@pytest.mark.asyncio
async def test_answer_question(ai_tutoring_service, mock_embeddings_service, mock_openai_service, mock_learning_style_service):
    # Setup test data
    user_id = "user123"
    question = "What is photosynthesis?"
    course_id = "course123"
    material_ids = ["material1", "material2"]
    confusion_level = 0  # No confusion
    
    # Mock learning style recommendations
    mock_learning_style_service.get_learning_style_recommendations.return_value = {
        "explanation_style": "detailed",
        "primary_style": "visual",
        "secondary_style": "reading"
    }
    
    # Mock similar content search
    mock_embeddings_service.search_similar_content.return_value = [
        {
            "content": "Photosynthesis is the process used by plants to convert light energy into chemical energy.",
            "similarity": 0.92,
            "material_id": "material1",
            "material_title": "Biology 101"
        },
        {
            "content": "During photosynthesis, plants take in carbon dioxide and water to produce glucose and oxygen.",
            "similarity": 0.85,
            "material_id": "material1",
            "material_title": "Biology 101"
        }
    ]
    
    # Mock OpenAI completion
    mock_openai_service.generate_completion.return_value = {
        "content": "Photosynthesis is the process by which plants convert light energy into chemical energy. This process takes place in the chloroplasts of plant cells, particularly in the leaves. During photosynthesis, plants take in carbon dioxide from the air and water from the soil. Using the energy from sunlight, they convert these ingredients into glucose (a sugar) and oxygen. The glucose serves as food for the plant, while the oxygen is released into the atmosphere.",
        "tokens_used": 150
    }
    
    # Call the method
    result = await ai_tutoring_service.answer_question(
        user_id=user_id,
        question=question,
        course_id=course_id,
        material_ids=material_ids,
        confusion_level=confusion_level
    )
    
    # Verify the result
    assert "answer" in result
    assert "tokens_used" in result
    assert result["tokens_used"] == 150
    
    # Verify learning style service was called
    mock_learning_style_service.get_learning_style_recommendations.assert_called_once_with(user_id)
    
    # Verify embeddings service was called
    mock_embeddings_service.search_similar_content.assert_called_once()
    call_args = mock_embeddings_service.search_similar_content.call_args[1]
    assert call_args["query"] == question
    assert call_args["material_ids"] == material_ids
    
    # Verify OpenAI service was called with appropriate context
    mock_openai_service.generate_completion.assert_called_once()
    call_args = mock_openai_service.generate_completion.call_args[1]
    assert any("detailed" in msg["content"] for msg in call_args["messages"])
    assert any("visual" in msg["content"] for msg in call_args["messages"])
    assert any("Photosynthesis is the process" in msg["content"] for msg in call_args["messages"])

@pytest.mark.asyncio
async def test_answer_question_with_confusion(ai_tutoring_service, mock_embeddings_service, mock_openai_service, mock_learning_style_service):
    # Setup test data
    user_id = "user123"
    question = "What is photosynthesis?"
    course_id = "course123"
    material_ids = ["material1", "material2"]
    confusion_level = 2  # High confusion
    
    # Mock learning style recommendations
    mock_learning_style_service.get_learning_style_recommendations.return_value = {
        "explanation_style": "simple",
        "primary_style": "auditory",
        "secondary_style": "kinesthetic"
    }
    
    # Mock similar content search
    mock_embeddings_service.search_similar_content.return_value = [
        {
            "content": "Photosynthesis is the process used by plants to convert light energy into chemical energy.",
            "similarity": 0.92,
            "material_id": "material1",
            "material_title": "Biology 101"
        }
    ]
    
    # Mock OpenAI completion
    mock_openai_service.generate_completion.return_value = {
        "content": "Photosynthesis is how plants make their own food. Think of it like cooking: plants take ingredients (sunlight, water, and carbon dioxide) and cook them together to make food (sugar) and release oxygen as a byproduct. This happens in the plant's leaves in special parts called chloroplasts.",
        "tokens_used": 120
    }
    
    # Call the method
    result = await ai_tutoring_service.answer_question(
        user_id=user_id,
        question=question,
        course_id=course_id,
        material_ids=material_ids,
        confusion_level=confusion_level
    )
    
    # Verify the result
    assert "answer" in result
    assert "tokens_used" in result
    assert result["tokens_used"] == 120
    
    # Verify OpenAI service was called with appropriate context for confusion
    mock_openai_service.generate_completion.assert_called_once()
    call_args = mock_openai_service.generate_completion.call_args[1]
    assert any("confusion level: 2" in msg["content"].lower() for msg in call_args["messages"])
    assert any("simple" in msg["content"] for msg in call_args["messages"])
    assert any("auditory" in msg["content"] for msg in call_args["messages"])

@pytest.mark.asyncio
async def test_answer_question_no_relevant_content(ai_tutoring_service, mock_embeddings_service, mock_openai_service, mock_learning_style_service):
    # Setup test data
    user_id = "user123"
    question = "What is quantum physics?"
    course_id = "course123"
    material_ids = ["material1", "material2"]
    
    # Mock learning style recommendations
    mock_learning_style_service.get_learning_style_recommendations.return_value = {
        "explanation_style": "balanced",
        "primary_style": "balanced"
    }
    
    # Mock empty similar content search
    mock_embeddings_service.search_similar_content.return_value = []
    
    # Mock OpenAI completion
    mock_openai_service.generate_completion.return_value = {
        "content": "I don't have specific information about quantum physics from your course materials. Quantum physics is a branch of physics that deals with the behavior of matter and energy at the smallest scales. Would you like me to provide some general information about quantum physics, or would you prefer to ask your instructor for course-specific materials?",
        "tokens_used": 100
    }
    
    # Call the method
    result = await ai_tutoring_service.answer_question(
        user_id=user_id,
        question=question,
        course_id=course_id,
        material_ids=material_ids
    )
    
    # Verify the result
    assert "answer" in result
    assert "tokens_used" in result
    assert result["tokens_used"] == 100
    
    # Verify OpenAI service was called with appropriate context
    mock_openai_service.generate_completion.assert_called_once()
    call_args = mock_openai_service.generate_completion.call_args[1]
    assert any("no relevant content found" in msg["content"].lower() for msg in call_args["messages"])

@pytest.mark.asyncio
async def test_explain_concept(ai_tutoring_service, mock_embeddings_service, mock_openai_service, mock_learning_style_service):
    # Setup test data
    user_id = "user123"
    concept = "photosynthesis"
    course_id = "course123"
    material_ids = ["material1", "material2"]
    detail_level = "detailed"
    
    # Mock learning style recommendations
    mock_learning_style_service.get_learning_style_recommendations.return_value = {
        "explanation_style": "detailed",
        "primary_style": "visual",
        "secondary_style": "reading"
    }
    
    # Mock similar content search
    mock_embeddings_service.search_similar_content.return_value = [
        {
            "content": "Photosynthesis is the process used by plants to convert light energy into chemical energy.",
            "similarity": 0.92,
            "material_id": "material1",
            "material_title": "Biology 101"
        }
    ]
    
    # Mock OpenAI completion
    mock_openai_service.generate_completion.return_value = {
        "content": "# Photosynthesis\n\nPhotosynthesis is the process by which plants convert light energy into chemical energy. This process takes place in the chloroplasts of plant cells, particularly in the leaves.\n\n## The Process\n1. Plants absorb water through their roots\n2. They take in carbon dioxide from the air through tiny pores called stomata\n3. Chlorophyll in the chloroplasts captures energy from sunlight\n4. This energy is used to convert water and carbon dioxide into glucose and oxygen\n5. Oxygen is released into the atmosphere\n6. Glucose is used by the plant for energy or stored for later use\n\n## Visual Representation\nImagine sunlight striking a leaf, where water molecules from the soil and carbon dioxide from the air combine in the chloroplasts to produce glucose molecules and oxygen molecules.",
        "tokens_used": 200
    }
    
    # Call the method
    result = await ai_tutoring_service.explain_concept(
        user_id=user_id,
        concept=concept,
        course_id=course_id,
        material_ids=material_ids,
        detail_level=detail_level
    )
    
    # Verify the result
    assert "explanation" in result
    assert "tokens_used" in result
    assert result["tokens_used"] == 200
    
    # Verify learning style service was called
    mock_learning_style_service.get_learning_style_recommendations.assert_called_once_with(user_id)
    
    # Verify embeddings service was called
    mock_embeddings_service.search_similar_content.assert_called_once()
    call_args = mock_embeddings_service.search_similar_content.call_args[1]
    assert call_args["query"] == concept
    assert call_args["material_ids"] == material_ids
    
    # Verify OpenAI service was called with appropriate context
    mock_openai_service.generate_completion.assert_called_once()
    call_args = mock_openai_service.generate_completion.call_args[1]
    assert any("detailed" in msg["content"] for msg in call_args["messages"])
    assert any("visual" in msg["content"] for msg in call_args["messages"])
    assert any("detail_level: detailed" in msg["content"] for msg in call_args["messages"])
