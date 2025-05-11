from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionTemplateService:
    """Service for managing question templates for quiz generation."""
    
    def __init__(self):
        """Initialize question templates."""
        # Define templates for different question types
        self.templates = {
            "multiple_choice": self._get_multiple_choice_templates(),
            "true_false": self._get_true_false_templates(),
            "short_answer": self._get_short_answer_templates(),
            "fill_in_blank": self._get_fill_in_blank_templates(),
            "matching": self._get_matching_templates()
        }
    
    def get_templates(self, question_type: str, difficulty: str = "medium") -> List[str]:
        """Get templates for a specific question type and difficulty.
        
        Args:
            question_type: Type of question (multiple_choice, true_false, etc.)
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            List of templates for the specified type and difficulty
        """
        if question_type not in self.templates:
            logger.warning(f"Unknown question type: {question_type}. Using multiple_choice.")
            question_type = "multiple_choice"
        
        templates = self.templates[question_type]
        
        # Filter by difficulty if specified
        if difficulty in ["easy", "medium", "hard"]:
            return [t for t in templates if t.get("difficulty") == difficulty or t.get("difficulty") == "any"]
        
        return templates
    
    def get_all_question_types(self) -> List[str]:
        """Get all available question types.
        
        Returns:
            List of all question types
        """
        return list(self.templates.keys())
    
    def _get_multiple_choice_templates(self) -> List[Dict[str, Any]]:
        """Get templates for multiple choice questions."""
        return [
            {
                "template": "What is {concept}?",
                "difficulty": "easy",
                "example": "What is machine learning?"
            },
            {
                "template": "Which of the following best describes {concept}?",
                "difficulty": "easy",
                "example": "Which of the following best describes reinforcement learning?"
            },
            {
                "template": "What is the primary purpose of {concept}?",
                "difficulty": "medium",
                "example": "What is the primary purpose of a neural network?"
            },
            {
                "template": "Which of the following is NOT a characteristic of {concept}?",
                "difficulty": "medium",
                "example": "Which of the following is NOT a characteristic of supervised learning?"
            },
            {
                "template": "How does {concept1} differ from {concept2}?",
                "difficulty": "hard",
                "example": "How does deep learning differ from traditional machine learning?"
            },
            {
                "template": "Which of the following would be the most appropriate application of {concept}?",
                "difficulty": "hard",
                "example": "Which of the following would be the most appropriate application of transfer learning?"
            }
        ]
    
    def _get_true_false_templates(self) -> List[Dict[str, Any]]:
        """Get templates for true/false questions."""
        return [
            {
                "template": "{concept} is a type of {category}.",
                "difficulty": "easy",
                "example": "Gradient descent is a type of optimization algorithm."
            },
            {
                "template": "{concept1} and {concept2} are the same thing.",
                "difficulty": "easy",
                "example": "Machine learning and deep learning are the same thing."
            },
            {
                "template": "The primary function of {concept} is to {function}.",
                "difficulty": "medium",
                "example": "The primary function of backpropagation is to update weights in a neural network."
            },
            {
                "template": "{concept} can only be used in {context}.",
                "difficulty": "medium",
                "example": "Convolutional neural networks can only be used in image processing."
            },
            {
                "template": "When implementing {concept}, it is necessary to {requirement}.",
                "difficulty": "hard",
                "example": "When implementing a recurrent neural network, it is necessary to handle vanishing gradients."
            },
            {
                "template": "The relationship between {concept1} and {concept2} is that {relationship}.",
                "difficulty": "hard",
                "example": "The relationship between bias and variance is that reducing one typically increases the other."
            }
        ]
    
    def _get_short_answer_templates(self) -> List[Dict[str, Any]]:
        """Get templates for short answer questions."""
        return [
            {
                "template": "Define {concept} in your own words.",
                "difficulty": "easy",
                "example": "Define machine learning in your own words."
            },
            {
                "template": "What is the purpose of {concept}?",
                "difficulty": "easy",
                "example": "What is the purpose of data normalization?"
            },
            {
                "template": "Explain how {concept} works.",
                "difficulty": "medium",
                "example": "Explain how backpropagation works."
            },
            {
                "template": "Compare and contrast {concept1} and {concept2}.",
                "difficulty": "medium",
                "example": "Compare and contrast supervised and unsupervised learning."
            },
            {
                "template": "Describe a real-world application of {concept} and explain why it is appropriate.",
                "difficulty": "hard",
                "example": "Describe a real-world application of reinforcement learning and explain why it is appropriate."
            },
            {
                "template": "What are the limitations of {concept} and how might they be addressed?",
                "difficulty": "hard",
                "example": "What are the limitations of neural networks and how might they be addressed?"
            }
        ]
    
    def _get_fill_in_blank_templates(self) -> List[Dict[str, Any]]:
        """Get templates for fill-in-the-blank questions."""
        return [
            {
                "template": "{concept} is defined as ___________.",
                "difficulty": "easy",
                "example": "Machine learning is defined as ___________."
            },
            {
                "template": "The main components of {concept} are ___________, ___________, and ___________.",
                "difficulty": "easy",
                "example": "The main components of a neural network are ___________, ___________, and ___________."
            },
            {
                "template": "In {concept}, the process of ___________ is used to ___________.",
                "difficulty": "medium",
                "example": "In gradient descent, the process of ___________ is used to ___________."
            },
            {
                "template": "The relationship between {concept1} and {concept2} is that ___________.",
                "difficulty": "medium",
                "example": "The relationship between precision and recall is that ___________."
            },
            {
                "template": "When implementing {concept}, one must consider ___________ because ___________.",
                "difficulty": "hard",
                "example": "When implementing a convolutional neural network, one must consider ___________ because ___________."
            },
            {
                "template": "The future of {concept} may involve ___________ which could lead to ___________.",
                "difficulty": "hard",
                "example": "The future of natural language processing may involve ___________ which could lead to ___________."
            }
        ]
    
    def _get_matching_templates(self) -> List[Dict[str, Any]]:
        """Get templates for matching questions."""
        return [
            {
                "template": "Match each {concept} with its definition.",
                "difficulty": "easy",
                "example": "Match each machine learning algorithm with its definition."
            },
            {
                "template": "Match each {concept} with its primary use case.",
                "difficulty": "easy",
                "example": "Match each neural network type with its primary use case."
            },
            {
                "template": "Match each {concept} with its corresponding {property}.",
                "difficulty": "medium",
                "example": "Match each optimization algorithm with its corresponding convergence properties."
            },
            {
                "template": "Match each {concept} with the problem it helps solve.",
                "difficulty": "medium",
                "example": "Match each regularization technique with the problem it helps solve."
            },
            {
                "template": "Match each {concept} with its advantages and disadvantages.",
                "difficulty": "hard",
                "example": "Match each deep learning architecture with its advantages and disadvantages."
            },
            {
                "template": "Match each {concept} with the appropriate scenario for its application.",
                "difficulty": "hard",
                "example": "Match each clustering algorithm with the appropriate scenario for its application."
            }
        ]

# Create a singleton instance of the QuestionTemplateService
question_template_service = QuestionTemplateService()
