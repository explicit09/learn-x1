from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user
from app.schemas.users import User
from app.services.vector_search import vector_search_service
from app.services.vector_database import vector_database_service

router = APIRouter()

@router.get("/search")
async def search_content(
    query: str = Query(..., description="Search query"),
    similarity_threshold: float = Query(0.7, description="Minimum similarity threshold (0-1)"),
    match_count: int = Query(5, description="Maximum number of matches to return"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Search for content similar to the query using vector similarity."""
    results = await vector_search_service.search_by_query(
        query=query,
        similarity_threshold=similarity_threshold,
        match_count=match_count
    )
    
    return {
        "query": query,
        "results": results,
        "result_count": len(results)
    }

@router.get("/answer")
async def answer_question(
    question: str = Query(..., description="Question to answer"),
    max_context_chunks: int = Query(3, description="Maximum number of context chunks to include"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Answer a question using relevant context from vector search."""
    result = await vector_search_service.answer_with_context(
        question=question,
        max_context_chunks=max_context_chunks
    )
    
    return {
        "question": question,
        "answer": result["answer"],
        "has_context": result["has_context"]
    }

@router.get("/related-materials")
async def find_related_materials(
    query: str = Query(..., description="Search query"),
    max_materials: int = Query(5, description="Maximum number of materials to return"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Find materials related to a query based on vector similarity."""
    materials = await vector_search_service.find_related_materials(
        query=query,
        max_materials=max_materials
    )
    
    return {
        "query": query,
        "materials": materials,
        "material_count": len(materials)
    }

@router.post("/process-material/{material_id}")
async def process_material_embeddings(
    material_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Process a material's content chunks for embeddings."""
    success = await vector_database_service.process_material_for_embeddings(material_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process material for embeddings")
    
    return {
        "material_id": material_id,
        "status": "success",
        "message": "Material processed for embeddings successfully"
    }
