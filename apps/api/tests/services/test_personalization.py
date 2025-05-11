import pytest
import asyncio
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta

from app.services.personalization import personalization_service

@pytest.fixture
def mock_prisma():
    """Mock the Prisma client."""
    with patch('app.services.personalization.prisma') as mock:
        # Mock user preference
        user_pref = MagicMock()
        user_pref.id = "pref-1"
        user_pref.userId = "user-1"
        user_pref.learning_style = "visual"
        user_pref.interests = json.dumps(["programming", "math"])
        user_pref.ui_preferences = json.dumps({"theme": "dark", "font_size": "large"})
        mock.userpreference.find_unique.return_value = user_pref
        
        # Mock learning style
        learning_style = MagicMock()
        learning_style.id = "style-1"
        learning_style.user_id = "user-1"
        learning_style.visual_score = 8
        learning_style.auditory_score = 6
        learning_style.reading_score = 7
        learning_style.kinesthetic_score = 5
        mock.learningstyle.find_unique.return_value = learning_style
        
        # Mock user
        user = MagicMock()
        user.id = "user-1"
        user.email = "test@example.com"
        user.organization = MagicMock()
        user.organization.id = "org-1"
        mock.user.find_unique.return_value = user
        
        # Mock materials
        material1 = MagicMock()
        material1.id = "material-1"
        material1.title = "Introduction to Programming"
        material1.type = "DOCUMENT"
        material1.topic = MagicMock()
        material1.topic.id = "topic-1"
        material1.topic.name = "Programming"
        
        material2 = MagicMock()
        material2.id = "material-2"
        material2.title = "Math Concepts"
        material2.type = "VIDEO"
        material2.topic = MagicMock()
        material2.topic.id = "topic-2"
        material2.topic.name = "Mathematics"
        
        mock.material.find_many.return_value = [material1, material2]
        
        # Mock user interactions
        interaction1 = MagicMock()
        interaction1.id = "interaction-1"
        interaction1.userId = "user-1"
        interaction1.materialId = "material-1"
        interaction1.type = "VIEW"
        interaction1.created_at = datetime.now() - timedelta(days=1)
        interaction1.material = material1
        
        interaction2 = MagicMock()
        interaction2.id = "interaction-2"
        interaction2.userId = "user-1"
        interaction2.materialId = "material-2"
        interaction2.type = "COMPLETE"
        interaction2.created_at = datetime.now() - timedelta(days=2)
        interaction2.material = material2
        
        mock.userinteraction.find_many.return_value = [interaction1, interaction2]
        
        # Mock quiz results
        quiz_result = MagicMock()
        quiz_result.id = "result-1"
        quiz_result.userId = "user-1"
        quiz_result.quizId = "quiz-1"
        quiz_result.score = 8
        quiz_result.possible_score = 10
        quiz_result.created_at = datetime.now() - timedelta(days=3)
        mock.quizresult.find_many.return_value = [quiz_result]
        
        yield mock

@pytest.fixture
def mock_learning_style_service():
    """Mock the learning style service."""
    with patch('app.services.personalization.learning_style_service') as mock:
        # Mock get_user_learning_style method
        mock.get_user_learning_style.return_value = {
            "id": "style-1",
            "user_id": "user-1",
            "visual_score": 8,
            "auditory_score": 6,
            "reading_score": 7,
            "kinesthetic_score": 5,
            "created_at": datetime.now() - timedelta(days=10),
            "updated_at": datetime.now() - timedelta(days=5)
        }
        
        yield mock

@pytest.mark.asyncio
async def test_get_user_preferences(mock_prisma, mock_learning_style_service):
    """Test getting user preferences."""
    # Call the get_user_preferences method
    preferences = await personalization_service.get_user_preferences("user-1")
    
    # Check that the preferences are as expected
    assert preferences["learning_style"] == "visual"
    assert "programming" in preferences["interests"]
    assert "math" in preferences["interests"]
    assert preferences["theme"] == "dark"
    assert preferences["font_size"] == "large"
    assert preferences["primary_learning_style"] == "visual"
    assert preferences["learning_style_details"]["visual_score"] == 8
    
    # Verify that the mock methods were called
    mock_prisma.userpreference.find_unique.assert_called_once_with(
        where={"userId": "user-1"}
    )
    mock_learning_style_service.get_user_learning_style.assert_called_once_with("user-1")

@pytest.mark.asyncio
async def test_update_user_preferences(mock_prisma):
    """Test updating user preferences."""
    # Preferences to update
    preferences = {
        "theme": "light",
        "font_size": "medium",
        "interests": ["programming", "science"],
        "learning_style": "auditory"
    }
    
    # Call the update_user_preferences method
    success = await personalization_service.update_user_preferences("user-1", preferences)
    
    # Check that the update was successful
    assert success is True
    
    # Verify that the mock method was called
    mock_prisma.userpreference.update.assert_called_once()
    
    # Check that the update data is correct
    update_call = mock_prisma.userpreference.update.call_args
    update_data = update_call[1]["data"]
    
    assert "ui_preferences" in update_data
    assert "interests" in update_data
    assert "learning_style" in update_data
    
    # Parse the JSON strings to check the values
    ui_prefs = json.loads(update_data["ui_preferences"])
    interests = json.loads(update_data["interests"])
    
    assert ui_prefs["theme"] == "light"
    assert ui_prefs["font_size"] == "medium"
    assert "programming" in interests
    assert "science" in interests
    assert update_data["learning_style"] == "auditory"

@pytest.mark.asyncio
async def test_get_personalized_recommendations(mock_prisma):
    """Test getting personalized recommendations."""
    # Call the get_personalized_recommendations method
    recommendations = await personalization_service.get_personalized_recommendations("user-1", limit=2)
    
    # Check that the recommendations are as expected
    assert len(recommendations) == 2
    assert recommendations[0]["id"] == "material-1"
    assert recommendations[0]["title"] == "Introduction to Programming"
    assert "Programming" in recommendations[0]["recommendation_reason"]
    
    # Verify that the mock methods were called
    mock_prisma.user.find_unique.assert_called_once_with(
        where={"id": "user-1"},
        include={"organization": True}
    )
    mock_prisma.material.find_many.assert_called_once()

@pytest.mark.asyncio
async def test_generate_personalized_study_plan(mock_prisma):
    """Test generating a personalized study plan."""
    # Call the generate_personalized_study_plan method
    study_plan = await personalization_service.generate_personalized_study_plan("user-1")
    
    # Check that the study plan is as expected
    assert study_plan["user_id"] == "user-1"
    assert "generated_at" in study_plan
    assert len(study_plan["topics"]) == 2
    assert study_plan["topics"][0]["name"] in ["Programming", "Mathematics"]
    assert len(study_plan["recommendations"]) > 0
    
    # Verify that the mock methods were called
    mock_prisma.user.find_unique.assert_called_once_with(
        where={"id": "user-1"},
        include={"organization": True}
    )
    mock_prisma.material.find_many.assert_called_once()

@pytest.mark.asyncio
async def test_get_adaptive_difficulty(mock_prisma):
    """Test getting adaptive difficulty."""
    # Call the get_adaptive_difficulty method
    difficulty = await personalization_service.get_adaptive_difficulty("user-1")
    
    # Check that the difficulty is as expected
    assert difficulty == "intermediate"  # Based on 8/10 score
    
    # Verify that the mock method was called
    mock_prisma.quizresult.find_many.assert_called_once()

@pytest.mark.asyncio
async def test_get_personalized_ui_settings(mock_prisma):
    """Test getting personalized UI settings."""
    # Call the get_personalized_ui_settings method
    ui_settings = await personalization_service.get_personalized_ui_settings("user-1")
    
    # Check that the UI settings are as expected
    assert ui_settings["theme"] == "dark"
    assert ui_settings["font_size"] == "large"
    assert "content_density" in ui_settings
    assert "animations" in ui_settings
    assert "language" in ui_settings
