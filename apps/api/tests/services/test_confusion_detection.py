import pytest
import asyncio
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

from app.services.confusion_detection import confusion_detection_service

@pytest.fixture
def mock_openai_service():
    """Mock the OpenAI service."""
    with patch('app.services.confusion_detection.openai_service') as mock:
        # Mock chat_completion method
        mock.chat_completion.return_value = json.dumps({
            "confusion_score": 0.8,
            "is_confused": True,
            "indicators": ["I don't understand", "confused"],
            "reasoning": "The text contains explicit confusion indicators"
        })
        
        yield mock

@pytest.fixture
def mock_prisma():
    """Mock the Prisma client."""
    with patch('app.services.confusion_detection.prisma') as mock:
        # Mock user interaction
        interaction = MagicMock()
        interaction.id = "interaction-1"
        interaction.type = "QUESTION"
        interaction.content = "I don't understand this concept. Can you explain it?"
        interaction.user = MagicMock()
        interaction.user.id = "user-1"
        interaction.material = MagicMock()
        interaction.material.id = "material-1"
        interaction.material.title = "Test Material"
        interaction.material.topic = MagicMock()
        interaction.material.topic.id = "topic-1"
        interaction.material.topic.name = "Test Topic"
        interaction.createdAt = datetime.now() - timedelta(days=1)
        
        mock.userinteraction.find_unique.return_value = interaction
        
        # Mock user interactions find_many
        mock.userinteraction.find_many.return_value = [interaction]
        
        # Mock user interactions count
        mock.userinteraction.count.return_value = 3
        
        # Mock user
        user = MagicMock()
        user.id = "user-1"
        user.first_name = "Test"
        user.last_name = "User"
        user.role = "STUDENT"
        user.organization = MagicMock()
        user.organization.id = "org-1"
        
        mock.user.find_unique.return_value = user
        mock.user.find_many.return_value = [user]
        
        # Mock learning style
        learning_style = MagicMock()
        learning_style.id = "style-1"
        learning_style.user_id = "user-1"
        learning_style.visual_score = 8
        learning_style.auditory_score = 6
        learning_style.reading_score = 7
        learning_style.kinesthetic_score = 5
        
        mock.learningstyle.find_unique.return_value = learning_style
        
        # Mock materials
        material = MagicMock()
        material.id = "material-1"
        material.title = "Test Material"
        material.type = "DOCUMENT"
        material.topic = MagicMock()
        material.topic.id = "topic-1"
        material.topic.name = "Test Topic"
        
        mock.material.find_many.return_value = [material]
        
        # Mock topic
        topic = MagicMock()
        topic.id = "topic-1"
        topic.name = "Test Topic"
        
        mock.topic.find_unique.return_value = topic
        
        # Mock quiz result
        quiz_result = MagicMock()
        quiz_result.id = "result-1"
        quiz_result.score = 7
        quiz_result.possible_score = 10
        
        mock.quizresult.find_many.return_value = [quiz_result]
        
        yield mock

@pytest.mark.asyncio
async def test_detect_confusion_in_text(mock_openai_service):
    """Test detecting confusion in text."""
    # Test with explicit confusion indicators
    result = await confusion_detection_service.detect_confusion_in_text(
        "I don't understand this concept at all. I'm really confused."
    )
    
    # Check that confusion was detected
    assert result["is_confused"] == True
    assert result["confusion_score"] > 0.7
    assert len(result["confusion_indicators"]) > 0
    assert "don't understand" in result["confusion_indicators"]
    
    # Test with no confusion indicators
    result = await confusion_detection_service.detect_confusion_in_text(
        "This concept makes perfect sense to me."
    )
    
    # Check that no confusion was detected by pattern matching
    # But NLP might still detect confusion, so we don't assert is_confused here
    assert len(result["confusion_indicators"]) == 0
    
    # Verify that the OpenAI service was called
    mock_openai_service.chat_completion.assert_called()

@pytest.mark.asyncio
async def test_detect_confusion_in_interaction(mock_prisma, mock_openai_service):
    """Test detecting confusion in an interaction."""
    # Test with a question interaction
    result = await confusion_detection_service.detect_confusion_in_interaction("interaction-1")
    
    # Check that confusion was detected
    assert result["is_confused"] == True
    assert result["confusion_score"] > 0.0
    assert len(result["confusion_indicators"]) > 0
    
    # Verify that the mock methods were called
    mock_prisma.userinteraction.find_unique.assert_called_once_with(
        where={"id": "interaction-1"},
        include={
            "user": True,
            "material": True
        }
    )

@pytest.mark.asyncio
async def test_analyze_user_confusion_patterns(mock_prisma, mock_openai_service):
    """Test analyzing user confusion patterns."""
    # Mock the detect_confusion_in_interaction method
    with patch.object(confusion_detection_service, 'detect_confusion_in_interaction') as mock_detect:
        mock_detect.return_value = {
            "is_confused": True,
            "confusion_score": 0.8,
            "confusion_indicators": ["don't understand"]
        }
        
        # Call the analyze_user_confusion_patterns method
        result = await confusion_detection_service.analyze_user_confusion_patterns("user-1", days=30)
        
        # Check that the analysis was performed
        assert result["user_id"] == "user-1"
        assert "confusion_level" in result
        assert "confused_topics" in result
        assert "confusion_trend" in result
        
        # Verify that the mock methods were called
        mock_prisma.userinteraction.find_many.assert_called_once()
        mock_detect.assert_called()

@pytest.mark.asyncio
async def test_get_intervention_recommendations(mock_prisma):
    """Test getting intervention recommendations."""
    # Mock the analyze_user_confusion_patterns method
    with patch.object(confusion_detection_service, 'analyze_user_confusion_patterns') as mock_analyze:
        mock_analyze.return_value = {
            "user_id": "user-1",
            "confusion_level": "high",
            "overall_confusion_score": 0.8,
            "confused_topics": [
                {
                    "id": "topic-1",
                    "name": "Test Topic",
                    "confusion_score": 0.8,
                    "confusion_rate": 0.7
                }
            ]
        }
        
        # Call the get_intervention_recommendations method
        result = await confusion_detection_service.get_intervention_recommendations("user-1")
        
        # Check that recommendations were generated
        assert result["user_id"] == "user-1"
        assert result["confusion_level"] == "high"
        assert result["needs_intervention"] == True
        assert len(result["recommendations"]) > 0
        assert len(result["resource_recommendations"]) > 0
        
        # Verify that the mock methods were called
        mock_analyze.assert_called_once_with("user-1")
        mock_prisma.learningstyle.find_unique.assert_called_once()

@pytest.mark.asyncio
async def test_detect_class_confusion_hotspots(mock_prisma):
    """Test detecting class confusion hotspots."""
    # Mock the analyze_user_confusion_patterns method
    with patch.object(confusion_detection_service, 'analyze_user_confusion_patterns') as mock_analyze:
        mock_analyze.return_value = {
            "user_id": "user-1",
            "confusion_level": "high",
            "overall_confusion_score": 0.8,
            "confused_topics": [
                {
                    "id": "topic-1",
                    "name": "Test Topic",
                    "confusion_score": 0.8,
                    "confusion_rate": 0.7
                }
            ]
        }
        
        # Call the detect_class_confusion_hotspots method
        result = await confusion_detection_service.detect_class_confusion_hotspots("org-1", days=30)
        
        # Check that hotspots were detected
        assert result["organization_id"] == "org-1"
        assert "hotspots" in result
        assert "confused_users" in result
        
        # Verify that the mock methods were called
        mock_prisma.user.find_many.assert_called_once()
        mock_analyze.assert_called()
