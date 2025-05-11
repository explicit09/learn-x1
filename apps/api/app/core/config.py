
import os
from pydantic import BaseModel, ConfigDict

class Settings(BaseModel):
    # API settings
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "LEARN-X API"
    VERSION: str = "1.0.0"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # JWT settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "test_secret_key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    
    # Feature flags
    ENABLE_AI_FEATURES: bool = os.getenv("ENABLE_AI_FEATURES", "true").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env"
    )

settings = Settings()
