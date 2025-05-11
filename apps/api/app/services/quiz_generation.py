from typing import List, Dict, Any, Optional
import logging
import json
import random
from prisma.models import Quiz, QuizQuestion, Material, Course
from app.services.openai import openai_service
from app.services.prisma import prisma
from app.services.question_templates import question_template_service
from app.services.ai_analytics import ai_analytics_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizGenerationService:
    """Service for generating quizzes from course materials."""
    
    async def generate_quiz(self, material_id: str, num_questions: int = 5, question_types: List[str] = None, difficulty: str = "medium", use_templates: bool = True) -> Dict[str, Any]:
        """Generate a quiz from a specific material.
        
        Args:
            material_id: ID of the material to generate quiz from
            num_questions: Number of questions to generate
            question_types: Types of questions to generate (multiple_choice, true_false, etc.)
            difficulty: Difficulty level (easy, medium, hard)
            use_templates: Whether to use question templates for generation
            
        Returns:
            Dictionary with quiz data and metadata
        """
        if question_types is None:
            question_types = ["multiple_choice", "true_false"]
        
        # Validate question types
        available_types = question_template_service.get_all_question_types()
        question_types = [qt for qt in question_types if qt in available_types]
        if not question_types:
            question_types = ["multiple_choice", "true_false"]
        
        # Validate difficulty
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"
        
        try:
            # Get the material
            material = await prisma.material.find_unique(
                where={"id": material_id},
                include={"course": True}
            )
            
            if not material:
                logger.error(f"Material not found: {material_id}")
                return {"error": "Material not found"}
            
            # Get question templates if enabled
            templates = []
            template_prompt = None
            if use_templates:
                for q_type in question_types:
                    templates.extend(question_template_service.get_templates(q_type, difficulty))
                
                # Shuffle and limit templates based on num_questions
                if templates:
                    random.shuffle(templates)
                    templates = templates[:num_questions]
                    
                    # Create template prompt
                    template_examples = ""
                    for i, template in enumerate(templates):
                        template_examples += f"Template {i+1}: {template['template']}"
                        template_examples += f"Example: {template['example']}"
                    
                    template_prompt = f"""
                    Use the following templates to generate {num_questions} {difficulty} difficulty questions:

{template_examples}
                    """
            
            # Generate quiz questions
            system_message = f"""
            You are an expert educational quiz generator. Your task is to create high-quality {difficulty} level quiz questions
            based on the provided content. The questions should test understanding and critical thinking, not just memorization.
            
            Guidelines for creating questions:
            1. For multiple choice questions:
               - Provide 4 options with only 1 correct answer
               - Make distractors plausible but clearly incorrect
               - Avoid using 'all of the above' or 'none of the above'
            
            2. For true/false questions:
               - Make statements that are clearly true or false based on the content
               - Avoid ambiguous statements
            
            3. For all questions:
               - Include a brief explanation of the correct answer
               - Ensure questions are directly related to the content
               - Vary the difficulty according to the specified level
               - For {difficulty} difficulty: {self._get_difficulty_guidelines(difficulty)}
            """
            
            # Add template instructions if provided
            if template_prompt:
                system_message += template_prompt
            
            try:
                questions = await openai_service.generate_quiz_questions(
                    content=material.content,
                    num_questions=num_questions,
                    question_types=question_types,
                    difficulty=difficulty,
                    system_message=system_message
                )
                
                if not questions:
                    logger.error("Failed to generate quiz questions")
                    return {"error": "Failed to generate quiz questions"}
            except Exception as e:
                logger.error(f"Error generating quiz questions: {str(e)}")
                return {"error": f"Failed to generate quiz questions: {str(e)}"}
            
            # Validate questions
            validated_questions = []
            for q in questions:
                validated_q = await self.validate_question(q)
                if validated_q:
                    validated_questions.append(validated_q)
                    
            if not validated_questions:
                logger.error("No valid questions generated")
                return {"error": "Failed to generate valid quiz questions"}
                
            questions = validated_questions
            
            # Create quiz in database
            quiz = await prisma.quiz.create(
                data={
                    "title": f"Quiz on {material.title}",
                    "description": f"Auto-generated quiz on {material.title}",
                    "course_id": material.course_id,
                    "material_id": material_id,
                    "difficulty": difficulty,
                    "time_limit": 10 * num_questions,  # 10 minutes per question
                }
            )
            
            # Create quiz questions in database
            db_questions = []
            for i, q in enumerate(questions):
                options = json.dumps(q.get("options", [])) if q.get("options") else None
                
                question = await prisma.quizquestion.create(
                    data={
                        "quiz_id": quiz.id,
                        "question_text": q["question_text"],
                        "question_type": q["question_type"],
                        "options": options,
                        "correct_answer": str(q["correct_answer"]),  # Convert to string for storage
                        "explanation": q.get("explanation", ""),
                        "points": 1,
                        "order": i + 1,
                    }
                )
                db_questions.append(question)
            
            return {
                "quiz_id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "num_questions": len(db_questions),
                "difficulty": difficulty,
                "time_limit": quiz.time_limit,
                "questions": questions  # Return the generated questions
            }
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return {"error": f"Failed to generate quiz: {str(e)}"}
    
    async def generate_quiz_from_course(self, course_id: str, num_questions: int = 10, question_types: List[str] = None, difficulty: str = "medium", use_templates: bool = True, adaptive: bool = False) -> Dict[str, Any]:
        """Generate a comprehensive quiz from all materials in a course.
        
        Args:
            course_id: ID of the course to generate quiz from
            num_questions: Total number of questions to generate
            question_types: Types of questions to generate
            difficulty: Difficulty level
            use_templates: Whether to use question templates for generation
            adaptive: Whether to generate adaptive questions based on student performance
            
        Returns:
            Dictionary with quiz data and metadata
        """
        if question_types is None:
            question_types = ["multiple_choice", "true_false"]
            
        # Validate question types
        available_types = question_template_service.get_all_question_types()
        question_types = [qt for qt in question_types if qt in available_types]
        if not question_types:
            question_types = ["multiple_choice", "true_false"]
        
        # Validate difficulty
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"
        
        try:
            # Get the course and its materials
            course = await prisma.course.find_unique(
                where={"id": course_id},
                include={"materials": True}
            )
            
            if not course:
                logger.error(f"Course not found: {course_id}")
                return {"error": "Course not found"}
            
            if not course.materials or len(course.materials) == 0:
                logger.error(f"No materials found for course: {course_id}")
                return {"error": "No materials found for this course"}
            
            # Determine how many questions to generate per material
            materials = course.materials
            questions_per_material = max(1, num_questions // len(materials))
            remaining_questions = num_questions % len(materials)
            
            # Generate questions for each material
            all_questions = []
            material_distribution = []
            
            for i, material in enumerate(materials):
                # Allocate questions to this material
                material_questions = questions_per_material
                if i < remaining_questions:
                    material_questions += 1
                
                if material_questions == 0:
                    continue
                
                # Generate questions for this material
                questions = await openai_service.generate_quiz_questions(
                    content=material.content,
                    num_questions=material_questions,
                    question_types=question_types,
                    difficulty=difficulty
                )
                
                if questions:
                    all_questions.extend(questions)
                    material_distribution.append({
                        "material_id": material.id,
                        "material_title": material.title,
                        "num_questions": len(questions)
                    })
            
            if not all_questions:
                logger.error("Failed to generate any quiz questions")
                return {"error": "Failed to generate quiz questions"}
            
            # Create quiz in database
            quiz = await prisma.quiz.create(
                data={
                    "title": f"Comprehensive Quiz for {course.title}",
                    "description": f"Auto-generated quiz covering all materials in {course.title}",
                    "course_id": course_id,
                    "difficulty": difficulty,
                    "time_limit": 10 * len(all_questions),  # 10 minutes per question
                }
            )
            
            # Create quiz questions in database
            db_questions = []
            for i, q in enumerate(all_questions):
                options = json.dumps(q.get("options", [])) if q.get("options") else None
                
                question = await prisma.quizquestion.create(
                    data={
                        "quiz_id": quiz.id,
                        "question_text": q["question_text"],
                        "question_type": q["question_type"],
                        "options": options,
                        "correct_answer": str(q["correct_answer"]),  # Convert to string for storage
                        "explanation": q.get("explanation", ""),
                        "points": 1,
                        "order": i + 1,
                    }
                )
                db_questions.append(question)
            
            return {
                "quiz_id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "num_questions": len(db_questions),
                "difficulty": difficulty,
                "time_limit": quiz.time_limit,
                "material_distribution": material_distribution,
                "questions": all_questions  # Return the generated questions
            }
        except Exception as e:
            logger.error(f"Error generating course quiz: {str(e)}")
            return {"error": f"Failed to generate course quiz: {str(e)}"}

    def _get_difficulty_guidelines(self, difficulty: str) -> str:
        """Get guidelines for a specific difficulty level.
        
        Args:
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Guidelines string for the specified difficulty
        """
        if difficulty == "easy":
            return "Focus on basic recall and understanding. Questions should test fundamental concepts and definitions."
        elif difficulty == "medium":
            return "Focus on application and analysis. Questions should require understanding relationships between concepts."
        elif difficulty == "hard":
            return "Focus on evaluation and synthesis. Questions should require critical thinking and applying concepts to new situations."
        else:
            return "Balance between recall, application, and critical thinking."
    
    async def validate_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a generated question for quality and correctness.
        
        Args:
            question: The question to validate
            
        Returns:
            Validated question with any corrections applied
        """
        try:
            # Basic validation checks
            if "question_text" not in question or not question["question_text"]:
                logger.error("Question missing question_text")
                return None
            
            if "question_type" not in question:
                logger.error("Question missing question_type")
                return None
            
            if "correct_answer" not in question:
                logger.error("Question missing correct_answer")
                return None
            
            # Type-specific validation
            if question["question_type"] == "multiple_choice":
                # Ensure options exist and are a list
                if "options" not in question or not isinstance(question["options"], list):
                    logger.error("Multiple choice question missing options list")
                    return None
                
                # Ensure there are at least 2 options
                if len(question["options"]) < 2:
                    logger.error("Multiple choice question has fewer than 2 options")
                    return None
                
                # Ensure correct answer is in options
                if question["correct_answer"] not in question["options"]:
                    logger.error("Multiple choice question correct answer not in options")
                    return None
            
            elif question["question_type"] == "true_false":
                # Ensure correct answer is boolean or string boolean
                if not isinstance(question["correct_answer"], bool) and question["correct_answer"].lower() not in ["true", "false"]:
                    logger.error("True/false question correct answer not boolean")
                    return None
            
            # Add explanation if missing
            if "explanation" not in question or not question["explanation"]:
                question["explanation"] = "No explanation provided."
            
            return question
        except Exception as e:
            logger.error(f"Error validating question: {str(e)}")
            return None

# Create a singleton instance of the QuizGenerationService
quiz_generation_service = QuizGenerationService()
