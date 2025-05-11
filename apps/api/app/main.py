from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.api.routes import auth, users, organizations, courses, materials, quizzes, ai, analytics, cost_optimization, ai_analytics_dashboard, vector_search, langchain_tutoring, context_retrieval, personalization, confusion_detection

# Initialize FastAPI app
app = FastAPI(
    title="LEARN-X API",
    description="API for the LEARN-X educational platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["organizations"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(materials.router, prefix="/api/materials", tags=["materials"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(cost_optimization.router, prefix="/api/cost-optimization", tags=["cost-optimization"])
app.include_router(ai_analytics_dashboard.router, prefix="/api/ai-analytics-dashboard", tags=["ai-analytics-dashboard"])
app.include_router(vector_search.router, prefix="/api/vector-search", tags=["vector-search"])
app.include_router(langchain_tutoring.router, prefix="/api/langchain-tutoring", tags=["langchain-tutoring"])
app.include_router(context_retrieval.router, prefix="/api/context-retrieval", tags=["context-retrieval"])
app.include_router(personalization.router, prefix="/api/personalization", tags=["personalization"])
app.include_router(confusion_detection.router, prefix="/api/confusion-detection", tags=["confusion-detection"])

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Welcome to LEARN-X API",
        "docs": "/docs",
        "version": settings.VERSION,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
