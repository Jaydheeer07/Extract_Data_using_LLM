from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Invoice Processing API"

    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_ORGANIZATION: str

    # OpenAI model configuration
    OPENAI_MODEL: str 

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_API_BASE: str
    OPENROUTER_MODEL: str
    
    # OpenRouter model options
    OPENROUTER_MODEL_MISTRAL: str 
    OPENROUTER_MODEL_QWEN: str 
    OPENROUTER_MODEL_GEMMA: str 

    # Database Configuration
    POSTGRES_CONNECTION_STRING: str = None

    # Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in the settings


@lru_cache()
def get_settings():
    """Get cached settings."""
    return Settings()


settings = get_settings()
