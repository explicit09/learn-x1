from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.base import DataResponse, PaginatedResponse, BaseResponse
from app.schemas.quiz import Quiz, QuizCreate, QuizUpdate, Question, QuestionCreate, QuestionUpdate, Submission, SubmissionCreate, SubmissionWithDetails
from app.services.auth import auth_service
from app.services.prisma import prisma_service

router = APIRouter()

@router.get("/course/{course_id}", response_model=PaginatedResponse[Quiz])
async def list_course_quizzes(
    course_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    published_only: bool = False,
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """List quizzes for a course with pagination."""
    # Get course
    course = await prisma_service.get(model="course", id=course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions - users can only see courses in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only see published courses and quizzes
    if current_user["role"] == "student":
        if course["status"] != "published":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Course not available"
            )
        published_only = True
    
    # Build filter conditions
    where = {"course_id": course_id}
    
    # Filter by published status
    if published_only:
        where["is_published"] = True
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get quizzes
    quizzes = await prisma_service.get_many(
        model="quiz",
        where=where,
        skip=skip,
        take=per_page,
        order_by={"title": "asc"}
    )
    
    # Get total count
    total = await prisma_service.count(model="quiz", where=where)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=quizzes,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages
        }
    )

@router.post("/", response_model=DataResponse[Quiz])
async def create_quiz(quiz_data: QuizCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Create a new quiz."""
    # Get course
    course = await prisma_service.get(model="course", id=quiz_data.course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions - only professors and admins can create quizzes in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # If material_id is provided, check if it exists and belongs to the course
    if quiz_data.material_id:
        material = await prisma_service.get(model="material", id=quiz_data.material_id)
        
        if not material or material["course_id"] != quiz_data.course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid material ID"
            )
    
    # Create quiz
    create_data = quiz_data.dict()
    create_data["course"] = {"connect": {"id": create_data["course_id"]}}
    del create_data["course_id"]
    
    if create_data.get("material_id"):
        create_data["material"] = {"connect": {"id": create_data["material_id"]}}
        del create_data["material_id"]
    
    new_quiz = await prisma_service.create(model="quiz", data=create_data)
    
    return DataResponse(data=new_quiz, message="Quiz created successfully")

@router.get("/{quiz_id}", response_model=DataResponse[Quiz])
async def get_quiz(quiz_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get quiz by ID."""
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - users can only see quizzes in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only see published courses and quizzes
    if current_user["role"] == "student" and (course["status"] != "published" or not quiz["is_published"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz not available"
        )
    
    return DataResponse(data=quiz)

@router.put("/{quiz_id}", response_model=DataResponse[Quiz])
async def update_quiz(quiz_id: str, quiz_update: QuizUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update quiz by ID."""
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - only professors and admins can update quizzes in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = quiz_update.dict(exclude_unset=True)
    
    # Update quiz
    updated_quiz = await prisma_service.update(
        model="quiz",
        id=quiz_id,
        data=update_data
    )
    
    return DataResponse(data=updated_quiz, message="Quiz updated successfully")

@router.delete("/{quiz_id}", response_model=BaseResponse)
async def delete_quiz(quiz_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Delete quiz by ID."""
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - only professors and admins can delete quizzes in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete quiz
    await prisma_service.delete(model="quiz", id=quiz_id)
    
    return BaseResponse(message="Quiz deleted successfully")

# Question endpoints
@router.get("/{quiz_id}/questions", response_model=PaginatedResponse[Question])
async def list_quiz_questions(
    quiz_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """List questions for a quiz with pagination."""
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - users can only see questions in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only see published courses and quizzes
    if current_user["role"] == "student" and (course["status"] != "published" or not quiz["is_published"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Questions not available"
        )
    
    # Build filter conditions
    where = {"quiz_id": quiz_id}
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get questions
    questions = await prisma_service.get_many(
        model="question",
        where=where,
        skip=skip,
        take=per_page,
        order_by={"order": "asc"}
    )
    
    # For students taking a quiz, hide correct answers
    if current_user["role"] == "student" and quiz["is_published"]:
        for question in questions:
            if "correct_answer" in question:
                del question["correct_answer"]
            if "explanation" in question:
                del question["explanation"]
    
    # Get total count
    total = await prisma_service.count(model="question", where=where)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=questions,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages
        }
    )

@router.post("/questions", response_model=DataResponse[Question])
async def create_question(question_data: QuestionCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Create a new question for a quiz."""
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=question_data.quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - only professors and admins can create questions in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Create question
    create_data = question_data.dict()
    create_data["quiz"] = {"connect": {"id": create_data["quiz_id"]}}
    del create_data["quiz_id"]
    
    new_question = await prisma_service.create(model="question", data=create_data)
    
    return DataResponse(data=new_question, message="Question created successfully")

@router.put("/questions/{question_id}", response_model=DataResponse[Question])
async def update_question(question_id: str, question_update: QuestionUpdate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Update question by ID."""
    # Get question
    question = await prisma_service.get(model="question", id=question_id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=question["quiz_id"])
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - only professors and admins can update questions in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prepare update data
    update_data = question_update.dict(exclude_unset=True)
    
    # Update question
    updated_question = await prisma_service.update(
        model="question",
        id=question_id,
        data=update_data
    )
    
    return DataResponse(data=updated_question, message="Question updated successfully")

@router.delete("/questions/{question_id}", response_model=BaseResponse)
async def delete_question(question_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Delete question by ID."""
    # Get question
    question = await prisma_service.get(model="question", id=question_id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=question["quiz_id"])
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - only professors and admins can delete questions in their organization
    if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete question
    await prisma_service.delete(model="question", id=question_id)
    
    return BaseResponse(message="Question deleted successfully")

# Submission endpoints
@router.post("/submissions", response_model=DataResponse[Submission])
async def submit_quiz(submission_data: SubmissionCreate, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Submit answers for a quiz."""
    # Get quiz
    quiz = await prisma_service.get(model="quiz", id=submission_data.quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get course
    course = await prisma_service.get(model="course", id=quiz["course_id"])
    
    # Check permissions - users can only submit quizzes in their organization
    if course["organization_id"] != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Students can only submit published courses and quizzes
    if current_user["role"] == "student" and (course["status"] != "published" or not quiz["is_published"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz not available for submission"
        )
    
    # Get all questions for the quiz
    questions = await prisma_service.get_many(
        model="question",
        where={"quiz_id": submission_data.quiz_id}
    )
    
    if not questions or len(questions) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz has no questions"
        )
    
    # Calculate score
    total_points = sum(q["points"] for q in questions)
    earned_points = 0
    question_results = []
    
    for question in questions:
        question_id = question["id"]
        user_answer = submission_data.answers.get(question_id)
        correct_answer = question["correct_answer"]
        is_correct = False
        
        # Check if answer is correct based on question type
        if question["question_type"] == "multiple_choice" or question["question_type"] == "true_false":
            is_correct = user_answer == correct_answer
        elif question["question_type"] == "short_answer":
            # Simple exact match for short answers
            is_correct = user_answer and user_answer.lower() == correct_answer.lower()
        elif question["question_type"] == "essay":
            # Essays are manually graded, so mark as pending
            is_correct = None
        
        # Add points if correct
        if is_correct:
            earned_points += question["points"]
        
        # Store result for this question
        question_results.append({
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": correct_answer if current_user["role"] != "student" else None,
            "is_correct": is_correct,
            "points": question["points"] if is_correct else 0,
            "max_points": question["points"],
            "explanation": question.get("explanation") if is_correct is not None else None
        })
    
    # Calculate percentage score
    score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    passed = score_percentage >= quiz["passing_score"]
    
    # Create submission
    create_data = {
        "quiz": {"connect": {"id": submission_data.quiz_id}},
        "user": {"connect": {"id": current_user["id"]}},
        "answers": submission_data.answers,
        "time_spent_seconds": submission_data.time_spent_seconds,
        "score": score_percentage,
        "passed": passed,
        "question_results": question_results
    }
    
    new_submission = await prisma_service.create(model="submission", data=create_data)
    
    return DataResponse(
        data=new_submission,
        message=f"Quiz submitted successfully. Score: {score_percentage:.1f}%. {'Passed!' if passed else 'Failed.'}"
    )

@router.get("/submissions/user", response_model=PaginatedResponse[Submission])
async def list_user_submissions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(auth_service.get_current_user)
) -> Any:
    """List quiz submissions for the current user with pagination."""
    # Build filter conditions
    where = {"user_id": current_user["id"]}
    
    # Calculate pagination
    skip = (page - 1) * per_page
    
    # Get submissions
    submissions = await prisma_service.get_many(
        model="submission",
        where=where,
        skip=skip,
        take=per_page,
        order_by={"created_at": "desc"}
    )
    
    # Get total count
    total = await prisma_service.count(model="submission", where=where)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=submissions,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages
        }
    )

@router.get("/submissions/{submission_id}", response_model=DataResponse[SubmissionWithDetails])
async def get_submission(submission_id: str, current_user: dict = Depends(auth_service.get_current_user)) -> Any:
    """Get submission by ID with detailed results."""
    # Get submission
    submission = await prisma_service.get(model="submission", id=submission_id)
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check permissions - users can only see their own submissions or professors/admins can see submissions for their courses
    if submission["user_id"] != current_user["id"]:
        # Get quiz
        quiz = await prisma_service.get(model="quiz", id=submission["quiz_id"])
        
        # Get course
        course = await prisma_service.get(model="course", id=quiz["course_id"])
        
        # Check if user is professor or admin in the same organization
        if current_user["role"] not in ["professor", "admin"] or course["organization_id"] != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Get quiz title
    quiz = await prisma_service.get(model="quiz", id=submission["quiz_id"])
    
    # Add quiz title to submission
    submission_with_details = {
        **submission,
        "quiz_title": quiz["title"]
    }
    
    return DataResponse(data=submission_with_details)
