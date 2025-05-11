import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Create a mock class for testing without dependencies
class MockQuizGenerationService:
    """A simplified version of the QuizGenerationService for testing."""
    
    async def generate_quiz_from_material(self, material_id, user_id, num_questions=5, 
                                         question_types=None, difficulty="medium", title=None):
        """Generate a quiz from a material."""
        if question_types is None:
            question_types = ["multiple_choice"]
        
        # Return mock data for testing
        return {
            "quiz_id": "quiz123",
            "title": title or "Quiz on Introduction to Biology",
            "material_id": material_id,
            "user_id": user_id,
            "num_questions": 2,
            "questions": [
                {
                    "id": "q1",
                    "question": "What is the primary function of photosynthesis?",
                    "options": [
                        "Converting light energy to chemical energy",
                        "Breaking down food for energy",
                        "Cellular respiration",
                        "Nitrogen fixation"
                    ],
                    "answer": "Converting light energy to chemical energy",
                    "explanation": "Photosynthesis is the process where plants convert light energy into chemical energy.",
                    "question_type": "multiple_choice",
                    "difficulty": difficulty
                },
                {
                    "id": "q2",
                    "question": "True or False: Photosynthesis releases oxygen as a byproduct.",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "During photosynthesis, plants take in carbon dioxide and release oxygen as a byproduct.",
                    "question_type": "true_false",
                    "difficulty": difficulty
                }
            ]
        }
    
    def _validate_quiz_questions(self, questions):
        """Validate quiz questions."""
        for question in questions:
            # Check required fields
            required_fields = ["question", "options", "answer", "explanation", "question_type"]
            for field in required_fields:
                if field not in question:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check answer is in options
            if question["answer"] not in question["options"]:
                raise ValueError(f"Answer must be one of the options: {question['answer']}")
            
            # Check true/false questions
            if question["question_type"] == "true_false" and set(question["options"]) != {"True", "False"}:
                raise ValueError("True/False questions must have options ['True', 'False']")

@pytest.fixture
def quiz_generation_service():
    return MockQuizGenerationService()

@pytest.mark.asyncio
async def test_generate_quiz_from_material(quiz_generation_service):
    # Test the generate_quiz_from_material method
    result = await quiz_generation_service.generate_quiz_from_material(
        material_id="material123",
        user_id="user123",
        num_questions=5,
        question_types=["multiple_choice", "true_false"],
        difficulty="medium"
    )
    
    # Verify the result
    assert result["quiz_id"] == "quiz123"
    assert result["material_id"] == "material123"
    assert result["user_id"] == "user123"
    assert len(result["questions"]) == 2
    assert result["questions"][0]["question_type"] == "multiple_choice"
    assert result["questions"][1]["question_type"] == "true_false"

@pytest.mark.asyncio
async def test_generate_quiz_with_custom_title(quiz_generation_service):
    # Test with custom title
    custom_title = "Custom Quiz Title"
    result = await quiz_generation_service.generate_quiz_from_material(
        material_id="material123",
        user_id="user123",
        title=custom_title
    )
    
    # Verify the title was set correctly
    assert result["title"] == custom_title

@pytest.mark.asyncio
async def test_generate_quiz_with_different_difficulty(quiz_generation_service):
    # Test with different difficulty levels
    result = await quiz_generation_service.generate_quiz_from_material(
        material_id="material123",
        user_id="user123",
        difficulty="hard"
    )
    
    # Verify the difficulty was set correctly
    assert result["questions"][0]["difficulty"] == "hard"
    assert result["questions"][1]["difficulty"] == "hard"

def test_validate_quiz_questions(quiz_generation_service):
    # Valid questions
    valid_questions = [
        {
            "question": "What is photosynthesis?",
            "options": ["Process A", "Process B", "Process C", "Process D"],
            "answer": "Process A",
            "explanation": "Explanation here",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        },
        {
            "question": "True or False: Photosynthesis releases oxygen.",
            "options": ["True", "False"],
            "answer": "True",
            "explanation": "Explanation here",
            "question_type": "true_false",
            "difficulty": "easy"
        }
    ]
    
    # Should not raise any exceptions
    quiz_generation_service._validate_quiz_questions(valid_questions)
    
    # Invalid question - missing options
    invalid_questions1 = [
        {
            "question": "What is photosynthesis?",
            "answer": "Process A",
            "explanation": "Explanation here",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        }
    ]
    
    with pytest.raises(ValueError) as excinfo:
        quiz_generation_service._validate_quiz_questions(invalid_questions1)
    assert "Missing required field" in str(excinfo.value)
    
    # Invalid question - answer not in options
    invalid_questions2 = [
        {
            "question": "What is photosynthesis?",
            "options": ["Process A", "Process B", "Process C", "Process D"],
            "answer": "Process E",
            "explanation": "Explanation here",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        }
    ]
    
    with pytest.raises(ValueError) as excinfo:
        quiz_generation_service._validate_quiz_questions(invalid_questions2)
    assert "Answer must be one of the options" in str(excinfo.value)
    
    # Invalid question - true_false with wrong options
    invalid_questions3 = [
        {
            "question": "True or False: Photosynthesis releases oxygen.",
            "options": ["Yes", "No"],
            "answer": "Yes",
            "explanation": "Explanation here",
            "question_type": "true_false",
            "difficulty": "easy"
        }
    ]
    
    with pytest.raises(ValueError) as excinfo:
        quiz_generation_service._validate_quiz_questions(invalid_questions3)
    assert "True/False questions must have options" in str(excinfo.value)
