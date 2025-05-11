import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from app.services.quiz_generation import QuizGenerationService
from app.services.openai import OpenAIService
from app.services.question_templates import QuestionTemplateService

@pytest.fixture
def mock_openai_service():
    with patch('app.services.quiz_generation.openai_service') as mock:
        mock.generate_quiz_questions = AsyncMock()
        yield mock

@pytest.fixture
def mock_question_template_service():
    with patch('app.services.quiz_generation.question_template_service') as mock:
        mock.get_templates_for_subject = AsyncMock()
        yield mock

@pytest.fixture
def mock_prisma():
    with patch('app.services.quiz_generation.prisma') as mock:
        # Mock Material model
        mock.material.find_unique = AsyncMock()
        
        # Mock Quiz model
        mock.quiz.create = AsyncMock()
        mock.quiz.update = AsyncMock()
        
        # Mock QuizQuestion model
        mock.quizquestion.create_many = AsyncMock()
        
        yield mock

@pytest.fixture
def quiz_generation_service():
    return QuizGenerationService()

@pytest.mark.asyncio
async def test_generate_quiz_from_material(quiz_generation_service, mock_openai_service, mock_question_template_service, mock_prisma):
    # Setup test data
    material_id = "material123"
    user_id = "user123"
    organization_id = "org123"
    num_questions = 5
    question_types = ["multiple_choice", "true_false"]
    difficulty = "medium"
    
    # Mock material data
    mock_material = MagicMock(
        id=material_id,
        title="Introduction to Biology",
        content="Photosynthesis is the process used by plants to convert light energy into chemical energy.",
        subject="Biology",
        organization_id=organization_id
    )
    mock_prisma.material.find_unique.return_value = mock_material
    
    # Mock question templates
    mock_question_template_service.get_templates_for_subject.return_value = [
        {
            "template": "What is the primary function of {concept}?",
            "question_type": "multiple_choice",
            "subject": "Biology"
        },
        {
            "template": "True or False: {statement}",
            "question_type": "true_false",
            "subject": "Biology"
        }
    ]
    
    # Mock generated questions
    mock_questions = [
        {
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
            "difficulty": "medium"
        },
        {
            "question": "True or False: Photosynthesis releases oxygen as a byproduct.",
            "options": ["True", "False"],
            "answer": "True",
            "explanation": "During photosynthesis, plants take in carbon dioxide and release oxygen as a byproduct.",
            "question_type": "true_false",
            "difficulty": "medium"
        }
    ]
    mock_openai_service.generate_quiz_questions.return_value = mock_questions
    
    # Mock quiz creation
    mock_quiz = MagicMock(
        id="quiz123",
        title="Quiz on Introduction to Biology",
        material_id=material_id,
        user_id=user_id,
        organization_id=organization_id
    )
    mock_prisma.quiz.create.return_value = mock_quiz
    
    # Call the method
    result = await quiz_generation_service.generate_quiz_from_material(
        material_id=material_id,
        user_id=user_id,
        num_questions=num_questions,
        question_types=question_types,
        difficulty=difficulty
    )
    
    # Verify the result
    assert result["quiz_id"] == "quiz123"
    assert result["title"] == "Quiz on Introduction to Biology"
    assert result["num_questions"] == len(mock_questions)
    
    # Verify material was retrieved
    mock_prisma.material.find_unique.assert_called_once_with(
        where={"id": material_id}
    )
    
    # Verify templates were retrieved
    mock_question_template_service.get_templates_for_subject.assert_called_once_with("Biology")
    
    # Verify questions were generated
    mock_openai_service.generate_quiz_questions.assert_called_once()
    call_args = mock_openai_service.generate_quiz_questions.call_args[1]
    assert call_args["content"] == mock_material.content
    assert call_args["num_questions"] == num_questions
    assert call_args["question_types"] == question_types
    assert call_args["difficulty"] == difficulty
    
    # Verify quiz was created
    mock_prisma.quiz.create.assert_called_once()
    create_args = mock_prisma.quiz.create.call_args[1]
    assert create_args["data"]["title"].startswith("Quiz on")
    assert create_args["data"]["material_id"] == material_id
    assert create_args["data"]["user_id"] == user_id
    assert create_args["data"]["organization_id"] == organization_id
    
    # Verify questions were created
    mock_prisma.quizquestion.create_many.assert_called_once()

@pytest.mark.asyncio
async def test_generate_quiz_from_material_not_found(quiz_generation_service, mock_prisma):
    # Mock material not found
    mock_prisma.material.find_unique.return_value = None
    
    # Call the method and expect an exception
    with pytest.raises(ValueError) as excinfo:
        await quiz_generation_service.generate_quiz_from_material(
            material_id="nonexistent",
            user_id="user123",
            num_questions=5
        )
    
    # Verify the error message
    assert "Material not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_generate_quiz_with_custom_title(quiz_generation_service, mock_openai_service, mock_question_template_service, mock_prisma):
    # Setup test data
    material_id = "material123"
    user_id = "user123"
    organization_id = "org123"
    custom_title = "Custom Quiz Title"
    
    # Mock material data
    mock_material = MagicMock(
        id=material_id,
        title="Introduction to Biology",
        content="Photosynthesis is the process used by plants to convert light energy into chemical energy.",
        subject="Biology",
        organization_id=organization_id
    )
    mock_prisma.material.find_unique.return_value = mock_material
    
    # Mock question templates
    mock_question_template_service.get_templates_for_subject.return_value = []
    
    # Mock generated questions
    mock_questions = [
        {
            "question": "What is photosynthesis?",
            "options": [
                "Converting light energy to chemical energy",
                "Breaking down food for energy",
                "Cellular respiration",
                "Nitrogen fixation"
            ],
            "answer": "Converting light energy to chemical energy",
            "explanation": "Photosynthesis is the process where plants convert light energy into chemical energy.",
            "question_type": "multiple_choice",
            "difficulty": "easy"
        }
    ]
    mock_openai_service.generate_quiz_questions.return_value = mock_questions
    
    # Mock quiz creation
    mock_quiz = MagicMock(
        id="quiz123",
        title=custom_title,
        material_id=material_id,
        user_id=user_id,
        organization_id=organization_id
    )
    mock_prisma.quiz.create.return_value = mock_quiz
    
    # Call the method with custom title
    result = await quiz_generation_service.generate_quiz_from_material(
        material_id=material_id,
        user_id=user_id,
        title=custom_title
    )
    
    # Verify the result
    assert result["quiz_id"] == "quiz123"
    assert result["title"] == custom_title
    
    # Verify quiz was created with custom title
    mock_prisma.quiz.create.assert_called_once()
    create_args = mock_prisma.quiz.create.call_args[1]
    assert create_args["data"]["title"] == custom_title

@pytest.mark.asyncio
async def test_validate_quiz_questions(quiz_generation_service):
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
    assert "Missing required fields" in str(excinfo.value)
    
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
