from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import settings
from app.schemas.base import DataResponse, PaginatedResponse, BaseResponse
from app.schemas.ai import AIInteractionCreate, AIInteraction, AISearchQuery, AISearchResult, AIQuizGenerationRequest, AIExplanationRequest, LearningStyleUpdate
from app.services.auth import auth_service
from app.services.prisma import prisma_service
from app.services.openai import openai_service
from app.services.ai_tutoring import ai_tutoring_service
from app.services.embeddings import embeddings_service
from app.services.quiz_generation import quiz_generation_service
from app.services.ai_analytics import ai_analytics_service

router = APIRouter()

# Learning styles endpoints
@router.get("/learning-style", response_model=DataResponse)
async def get_learning_style(current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get the current user's learning style preferences."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    try:
        from app.services.learning_styles import learning_style_service
        
        # Get user's learning style
        learning_style = await learning_style_service.get_user_learning_style(current_user["id"])
        
        if not learning_style:
            # Return default values if no learning style found
            return DataResponse(
                message="Default learning style preferences",
                data={
                    "visual_score": 5,
                    "auditory_score": 5,
                    "reading_score": 5,
                    "kinesthetic_score": 5
                }
            )
        
        return DataResponse(
            message="Learning style preferences retrieved successfully",
            data=learning_style
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving learning style: {str(e)}"
        )

@router.put("/learning-style", response_model=DataResponse)
async def update_learning_style(style_data: LearningStyleUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update the current user's learning style preferences."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    try:
        from app.services.learning_styles import learning_style_service
        
        # Update user's learning style
        updated_style = await learning_style_service.update_user_learning_style(
            user_id=current_user["id"],
            style_data=style_data.dict()
        )
        
        if not updated_style:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update learning style"
            )
        
        return DataResponse(
            message="Learning style preferences updated successfully",
            data=updated_style
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating learning style: {str(e)}"
        )

@router.get("/learning-recommendations", response_model=DataResponse)
async def get_learning_recommendations(current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get personalized learning recommendations based on learning style."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    try:
        from app.services.learning_styles import learning_style_service
        
        # Get learning recommendations
        recommendations = await learning_style_service.get_learning_style_recommendations(current_user["id"])
        
        return DataResponse(
            message="Learning recommendations retrieved successfully",
            data=recommendations
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving learning recommendations: {str(e)}"
        )

# Add analytics endpoints
@router.get("/analytics/usage", response_model=DataResponse)
async def get_ai_usage_metrics(
    time_period: str = Query("week", description="Time period for metrics (day, week, month)"),
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """Get AI usage metrics for the organization."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Check permissions - only professors and admins can view analytics
    if current_user["role"] not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        metrics = await ai_analytics_service.get_usage_metrics(
            organization_id=current_user["organization_id"],
            time_period=time_period
        )
        
        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=metrics["error"]
            )
        
        return DataResponse(
            message=f"AI usage metrics for {time_period}",
            data=metrics
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving usage metrics: {str(e)}"
        )

@router.get("/analytics/performance", response_model=DataResponse)
async def get_ai_performance_metrics(
    time_period: str = Query("week", description="Time period for metrics (day, week, month)"),
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """Get AI performance metrics for the organization."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Check permissions - only professors and admins can view analytics
    if current_user["role"] not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        metrics = await ai_analytics_service.get_performance_metrics(
            organization_id=current_user["organization_id"],
            time_period=time_period
        )
        
        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=metrics["error"]
            )
        
        return DataResponse(
            message=f"AI performance metrics for {time_period}",
            data=metrics
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving performance metrics: {str(e)}"
        )

@router.post("/process-material", response_model=DataResponse)
async def process_material_for_ai(
    material_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """Process a material for AI features (generate embeddings, etc.)."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Check permissions - only professors and admins can process materials
    if current_user["role"] not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Validate material
    material = await prisma_service.get(model="material", id=material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check if course is in user's organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access material from another organization"
        )
    
    try:
        # Process the material content and generate embeddings
        chunk_ids = await embeddings_service.process_material_content(material_id)
        
        return DataResponse(
            message=f"Material processed successfully with {len(chunk_ids)} content chunks",
            data={
                "material_id": material_id,
                "chunk_count": len(chunk_ids),
                "chunk_ids": chunk_ids
            }
        )
    except Exception as e:
        # Log the error
        await ai_analytics_service.log_error(
            error_type="MATERIAL_PROCESSING_ERROR",
            error_message=str(e),
            user_id=current_user["id"],
            metadata={"material_id": material_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing material: {str(e)}"
        )

@router.post("/generate-course-quiz", response_model=DataResponse)
async def generate_course_quiz(
    course_id: str,
    num_questions: int = Query(10, description="Number of questions to generate"),
    difficulty: str = Query("medium", description="Difficulty level (easy, medium, hard)"),
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """Generate a comprehensive quiz from all materials in a course."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Check permissions - only professors and admins can generate quizzes
    if current_user["role"] not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Validate course
    course = await prisma_service.get(model="course", id=course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course is in user's organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access course from another organization"
        )
    
    try:
        # Generate quiz from course materials
        quiz_result = await quiz_generation_service.generate_quiz_from_course(
            course_id=course_id,
            num_questions=num_questions,
            difficulty=difficulty
        )
        
        if "error" in quiz_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=quiz_result["error"]
            )
        
        return DataResponse(
            message=f"Course quiz generated successfully with {quiz_result['num_questions']} questions",
            data=quiz_result
        )
    except Exception as e:
        # Log the error
        await ai_analytics_service.log_error(
            error_type="COURSE_QUIZ_GENERATION_ERROR",
            error_message=str(e),
            user_id=current_user["id"],
            metadata={"course_id": course_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating course quiz: {str(e)}"
        )

@router.post("/ask", response_model=DataResponse[AIInteraction])
async def ask_ai(interaction_data: AIInteractionCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Ask a question to the AI assistant."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Validate course and material if provided
    if interaction_data.course_id:
        course = await prisma_service.get(model="course", id=interaction_data.course_id)
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Check if course is in user's organization
        if course["organization_id"] != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access course from another organization"
            )
        
        # Students can only access published courses
        if current_user["role"] == "student" and course["status"] != "published":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Course not available"
            )
    
    if interaction_data.material_id:
        material = await prisma_service.get(model="material", id=interaction_data.material_id)
        
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )
        
        # Check if material belongs to the specified course
        if interaction_data.course_id and material["course_id"] != interaction_data.course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Material does not belong to the specified course"
            )
        
        # Get course if not already validated
        if not interaction_data.course_id:
            course = await prisma_service.get(model="course", id=material["course_id"])
            
            # Check if course is in user's organization
            if course["organization_id"] != current_user["organization_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access material from another organization"
                )
            
            # Students can only access published courses and materials
            if current_user["role"] == "student" and (course["status"] != "published" or not material["is_published"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Material not available"
                )
    
    # Process context IDs if provided
    context_content = []
    if interaction_data.context_ids and len(interaction_data.context_ids) > 0:
        for chunk_id in interaction_data.context_ids:
            chunk = await prisma_service.get(model="contentChunk", id=chunk_id)
            if chunk:
                context_content.append(chunk["content"])
    
    # Use AI tutoring service to generate a response
    try:
        ai_response = await ai_tutoring_service.answer_question(
            user_id=current_user["id"],
            query=interaction_data.query,
            course_id=interaction_data.course_id,
            material_id=interaction_data.material_id
        )
        
        if "error" in ai_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ai_response["error"]
            )
        
        # Create AI interaction record
        create_data = interaction_data.dict()
        create_data["user"] = {"connect": {"id": current_user["id"]}}
        
        if create_data.get("course_id"):
            create_data["course"] = {"connect": {"id": create_data["course_id"]}}
            del create_data["course_id"]
        
        if create_data.get("material_id"):
            create_data["material"] = {"connect": {"id": create_data["material_id"]}}
            del create_data["material_id"]
        
        # Use the response from the AI tutoring service
        create_data["response"] = ai_response["response"]
        create_data["confusion_level"] = ai_response.get("confusion_level", 5)
        create_data["tokens_used"] = len(interaction_data.query) + len(ai_response["response"])
    except Exception as e:
        # Log the error
        await ai_analytics_service.log_error(
            error_type="AI_TUTORING_ERROR",
            error_message=str(e),
            user_id=current_user["id"],
            metadata={"query": interaction_data.query}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating AI response: {str(e)}"
        )
    
    new_interaction = await prisma_service.create(model="aiInteraction", data=create_data)
    
    return DataResponse(data=new_interaction)

@router.post("/search", response_model=DataResponse[List[AISearchResult]])
async def semantic_search(search_data: AISearchQuery, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Perform semantic search on content chunks."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Validate course if provided
    if search_data.course_id:
        course = await prisma_service.get(model="course", id=search_data.course_id)
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Check if course is in user's organization
        if course["organization_id"] != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access course from another organization"
            )
        
        # Students can only access published courses
        if current_user["role"] == "student" and course["status"] != "published":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Course not available"
            )
    
    # Use embeddings service for semantic search
    try:
        search_results = await embeddings_service.search_similar_content(search_data.query, limit=search_data.limit or 5)
        
        # Filter results by course if specified
        if search_data.course_id and search_results:
            search_results = [r for r in search_results if r.get("course_id") == search_data.course_id]
        
        # Transform results to match the expected schema
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "content_chunk_id": result.get("id"),
                "content": result.get("content"),
                "material_id": result.get("material_id"),
                "material_title": result.get("title", "Unknown"),
                "similarity": result.get("similarity", 0),
                "metadata": result.get("metadata", {})
            })
        
        # If no results found through vector search, return empty list
        if not formatted_results:
            formatted_results = []
    except Exception as e:
        # Log the error
        await ai_analytics_service.log_error(
            error_type="SEMANTIC_SEARCH_ERROR",
            error_message=str(e),
            user_id=current_user["id"],
            metadata={"query": search_data.query}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing semantic search: {str(e)}"
        )
    
    return DataResponse(data=formatted_results)

@router.post("/generate-quiz", response_model=DataResponse)
async def generate_quiz(generation_data: AIQuizGenerationRequest, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Generate a quiz based on material content using AI."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Check permissions - only professors and admins can generate quizzes
    if current_user["role"] not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Validate material
    material = await prisma_service.get(model="material", id=generation_data.material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=material["course_id"])
    
    # Check if course is in user's organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access material from another organization"
        )
    
    # Use quiz generation service to create a quiz
    try:
        quiz_result = await quiz_generation_service.generate_quiz(
            material_id=generation_data.material_id,
            num_questions=generation_data.num_questions,
            question_types=generation_data.question_types,
            difficulty=generation_data.difficulty
        )
        
        if "error" in quiz_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=quiz_result["error"]
            )
        
        return DataResponse(
            message=f"Quiz generated successfully with {quiz_result['num_questions']} questions",
            data=quiz_result
        )
    except Exception as e:
        # Log the error
        await ai_analytics_service.log_error(
            error_type="QUIZ_GENERATION_ERROR",
            error_message=str(e),
            user_id=current_user["id"],
            metadata={"material_id": generation_data.material_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating quiz: {str(e)}"
        )

@router.post("/explain", response_model=DataResponse)
async def explain_content(explanation_data: AIExplanationRequest, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get an AI explanation for specific content."""
    # Check if AI features are enabled
    if not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI features are not enabled"
        )
    
    # Validate material if provided
    if explanation_data.material_id:
        material = await prisma_service.get(model="material", id=explanation_data.material_id)
        
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )
        
        # Get course
        course = await prisma_service.get(model="course", id=material["course_id"])
        
        # Check if course is in user's organization
        if course["organization_id"] != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access material from another organization"
            )
        
        # Students can only access published courses and materials
        if current_user["role"] == "student" and (course["status"] != "published" or not material["is_published"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Material not available"
            )
    
    try:
        # Prepare system message for explanation
        system_message = """
        You are an educational AI assistant. Your task is to explain the given content in a clear, concise, and educational manner.
        Provide examples where appropriate and break down complex concepts into simpler terms.
        Use markdown formatting to make your explanation more readable.
        """
        
        # Generate explanation using OpenAI service
        explanation = await openai_service.generate_completion(
            prompt=f"Please explain the following content in detail: {explanation_data.content}",
            system_message=system_message,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Create AI interaction record for analytics
        await prisma_service.create(
            model="aiInteraction",
            data={
                "user": {"connect": {"id": current_user["id"]}},
                "query": f"Explain: {explanation_data.content[:100]}...",
                "response": explanation,
                "tokens_used": len(explanation_data.content) + len(explanation),
                "interaction_type": "explanation"
            }
        )
        
        return DataResponse(
            message="Explanation generated successfully",
            data={
                "explanation": explanation,
                "original_content": explanation_data.content
            }
        )
    except Exception as e:
        # Log the error
        await ai_analytics_service.log_error(
            error_type="EXPLANATION_ERROR",
            error_message=str(e),
            user_id=current_user["id"],
            metadata={"content_length": len(explanation_data.content)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating explanation: {str(e)}"
        )
    
    # TODO: Implement actual AI explanation using OpenAI or similar service
    # For now, return a mock response
    
    # Mock response
    create_data["response"] = f"This is a mock explanation for: {explanation_data.question} (Detail level: {explanation_data.detail_level})"
    create_data["tokens_used"] = len(explanation_data.question) + len(create_data["response"])
    
    new_interaction = await prisma_service.create(model="aiInteraction", data=create_data)
    
    return DataResponse(data=new_interaction)
