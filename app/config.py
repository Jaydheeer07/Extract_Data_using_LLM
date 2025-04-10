import os
from functools import lru_cache
import streamlit as st
from typing import Optional

from pydantic_settings import BaseSettings


# First check if we're running in Streamlit
def get_streamlit_secrets():
    """Get secrets from Streamlit if available"""
    secrets = {}
    if 'streamlit' in globals() or 'st' in globals():
        try:
            if hasattr(st, 'secrets'):
                print("Found Streamlit secrets, converting to uppercase")
                # Convert all keys to uppercase to match environment variable style
                for key, value in st.secrets.items():
                    secrets[key.upper()] = value
                    print(f"Loaded secret: {key.upper()}")
            else:
                print("No st.secrets attribute found")
        except Exception as e:
            print(f"Error loading Streamlit secrets: {str(e)}")
            pass
    else:
        print("Streamlit not in globals")
    return secrets


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Invoice Processing API"

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORGANIZATION: Optional[str] = None

    # OpenAI model configuration
    OPENAI_MODEL: Optional[str] = "gpt-4o"

    # OpenRouter Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_API_BASE: Optional[str] = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: Optional[str] = "qwen/qwen2.5-vl-32b-instruct:free"
    
    # OpenRouter model options
    OPENROUTER_MODEL_MISTRAL: Optional[str] = "mistralai/mistral-small-3.1-24b-instruct"
    OPENROUTER_MODEL_QWEN: Optional[str] = "qwen/qwen2.5-vl-32b-instruct:free"
    OPENROUTER_MODEL_GEMMA: Optional[str] = "google/gemma-3-27b-it"
    OPENROUTER_MODEL_GPT: Optional[str] = "openai/gpt-4o-mini"
    OPENROUTER_MODEL_LLAMA: Optional[str] = "meta-llama/llama-4-maverick"
    OPENROUTER_MODEL_GEMINI: Optional[str] = "google/gemini-2.0-flash-001"
    OPENROUTER_MODEL_AMAZON: Optional[str] = "amazon/nova-lite-v1"

    # Database Configuration
    POSTGRES_CONNECTION_STRING: Optional[str] = None

    # Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in the settings
        
        # Allow environment variables to override
        env_prefix = ""
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    """Get cached settings."""
    # First try to get settings from Streamlit secrets
    streamlit_secrets = get_streamlit_secrets()
    print(f"Loaded {len(streamlit_secrets)} secrets from Streamlit")
    
    # Create settings with environment variables and then update with Streamlit secrets
    settings_instance = Settings()
    
    # Override with Streamlit secrets if available
    for key, value in streamlit_secrets.items():
        if hasattr(settings_instance, key):
            setattr(settings_instance, key, value)
            print(f"Applied setting: {key}")
        else:
            print(f"Warning: Secret {key} found but no matching setting in Settings class")
    
    # Debug output for important settings
    print(f"OPENROUTER_API_KEY set: {bool(settings_instance.OPENROUTER_API_KEY)}")
    print(f"POSTGRES_CONNECTION_STRING set: {bool(settings_instance.POSTGRES_CONNECTION_STRING)}")
    
    return settings_instance


settings = get_settings()
