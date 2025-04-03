from openai import OpenAI   
from app.config import settings
import logging
import streamlit as st

logger = logging.getLogger(__name__)

#client = OpenAI(
 #   api_key=settings.OPENAI_API_KEY, organization=settings.OPENAI_ORGANIZATION
#)

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_API_BASE
)

# Get the model from session state if available, otherwise use default from settings
def get_current_model():
    if st.session_state and hasattr(st, 'session_state') and 'selected_model' in st.session_state:
        current_model = st.session_state.selected_model
        logger.info(f"Using model from session state: {current_model}")
        return current_model
    else:
        logger.info(f"Using default model from settings: {settings.OPENROUTER_MODEL}")
        return settings.OPENROUTER_MODEL

# Default model from settings
model = settings.OPENROUTER_MODEL
logger.info(f"Default model loaded: {model}")
