from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Create a simple FastAPI app for testing
app = FastAPI(
    title="LEARN-X API Test",
    description="Simple test API for the LEARN-X platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a simple model
class User(BaseModel):
    id: str
    name: str
    email: str
    role: str

# Sample data
users = [
    User(id="1", name="John Doe", email="john@example.com", role="admin"),
    User(id="2", name="Jane Smith", email="jane@example.com", role="professor"),
    User(id="3", name="Bob Johnson", email="bob@example.com", role="student"),
]

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Welcome to LEARN-X API Test",
        "docs": "/docs",
        "version": "0.1.0",
    }

# Get all users
@app.get("/api/users", tags=["users"])
async def get_users():
    return users

# Get user by ID
@app.get("/api/users/{user_id}", tags=["users"])
async def get_user(user_id: str):
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    print("Starting simplified LEARN-X API test server...")
    uvicorn.run("simple_test:app", host="127.0.0.1", port=8080, reload=True)
