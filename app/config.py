import os
from functools import lru_cache
import streamlit as st

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Invoice Processing API"

    # OpenAI Configuration
    OPENAI_API_KEY: str = None
    OPENAI_ORGANIZATION: str = None

    # OpenAI model configuration
    OPENAI_MODEL: str = None

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = None
    OPENROUTER_API_BASE: str = None
    OPENROUTER_MODEL: str = "mistralai/mistral-small-3.1-24b-instruct"
    
    # OpenRouter model options
    OPENROUTER_MODEL_MISTRAL: str = "mistralai/mistral-small-3.1-24b-instruct"
    OPENROUTER_MODEL_QWEN: str = "qwen/qwen2.5-vl-32b-instruct:free"
    OPENROUTER_MODEL_GEMMA: str = "google/gemma-3-12b-it"

    # Database Configuration
    POSTGRES_CONNECTION_STRING: str = None

    # Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in the settings
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Check for Streamlit secrets and override settings if available
        if hasattr(st, 'secrets'):
            # OpenAI settings
            if 'openai_api_key' in st.secrets:
                self.OPENAI_API_KEY = st.secrets['openai_api_key']
            if 'openai_organization' in st.secrets:
                self.OPENAI_ORGANIZATION = st.secrets['openai_organization']
            if 'openai_model' in st.secrets:
                self.OPENAI_MODEL = st.secrets['openai_model']
                
            # OpenRouter settings
            if 'openrouter_api_key' in st.secrets:
                self.OPENROUTER_API_KEY = st.secrets['openrouter_api_key']
            if 'openrouter_api_base' in st.secrets:
                self.OPENROUTER_API_BASE = st.secrets['openrouter_api_base']
            if 'openrouter_model' in st.secrets:
                self.OPENROUTER_MODEL = st.secrets['openrouter_model']
            if 'openrouter_model_mistral' in st.secrets:
                self.OPENROUTER_MODEL_MISTRAL = st.secrets['openrouter_model_mistral']
            if 'openrouter_model_qwen' in st.secrets:
                self.OPENROUTER_MODEL_QWEN = st.secrets['openrouter_model_qwen']
            if 'openrouter_model_gemma' in st.secrets:
                self.OPENROUTER_MODEL_GEMMA = st.secrets['openrouter_model_gemma']
                
            # Database settings
            if 'postgres_connection_string' in st.secrets:
                self.POSTGRES_CONNECTION_STRING = st.secrets['postgres_connection_string']


@lru_cache()
def get_settings():
    """Get cached settings."""
    return Settings()


settings = get_settings()
