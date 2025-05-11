from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import UUID4

from app.schemas.user import User
from app.api.deps import get_current_user
from app.services.context_retrieval import context_retrieval_service

router = APIRouter()

@router.get("/retrieve")
async def retrieve_context(
    query: str = Query(..., description="The query to retrieve context for"),
    material_id: Optional[str] = Query(None, description="Optional material ID to limit context to"),
    topic_id: Optional[str] = Query(None, description="Optional topic ID to limit context to"),
    similarity_threshold: float = Query(0.7, description="Minimum similarity threshold (0-1)"),
    match_count: int = Query(5, description="Maximum number of matches to return"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Retrieve relevant context for a query."""
    results = await context_retrieval_service.retrieve_context(
        query=query,
        user_id=current_user.id,
        material_id=material_id,
        topic_id=topic_id,
        similarity_threshold=similarity_threshold,
        match_count=match_count
    )
    
    return {
        "query": query,
        "results": results,
        "result_count": len(results)
    }

@router.get("/hybrid")
async def retrieve_hybrid_context(
    query: str = Query(..., description="The query to retrieve context for"),
    match_count: int = Query(5, description="Maximum number of matches to return"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Retrieve context using hybrid search (vector + keyword)."""
    results = await context_retrieval_service.retrieve_hybrid_context(
        query=query,
        user_id=current_user.id,
        match_count=match_count
    )
    
    return {
        "query": query,
        "results": results,
        "result_count": len(results)
    }

@router.get("/multi-query")
async def retrieve_multi_query_context(
    query: str = Query(..., description="The main query to retrieve context for"),
    match_count: int = Query(5, description="Maximum number of matches to return per query"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Retrieve context using multiple queries for complex questions."""
    # Generate sub-queries
    sub_queries = await context_retrieval_service.generate_sub_queries(query)
    
    # Retrieve context using multi-query approach
    results = await context_retrieval_service.retrieve_multi_query_context(
        main_query=query,
        sub_queries=sub_queries,
        user_id=current_user.id,
        match_count=match_count
    )
    
    return {
        "main_query": query,
        "sub_queries": sub_queries,
        "results": results,
        "result_count": len(results)
    }

@router.get("/for-question")
async def get_context_for_question(
    question: str = Query(..., description="The question to get context for"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get formatted context for a question, optimized for LLM use."""
    formatted_context, raw_context = await context_retrieval_service.get_context_for_question(
        question=question,
        user_id=current_user.id
    )
    
    return {
        "question": question,
        "formatted_context": formatted_context,
        "raw_context": raw_context,
        "context_chunk_count": len(raw_context)
    }
