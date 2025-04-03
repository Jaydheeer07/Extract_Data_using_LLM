from openai import OpenAI   
from app.config import settings
import logging

logger = logging.getLogger(__name__)

#client = OpenAI(
 #   api_key=settings.OPENAI_API_KEY, organization=settings.OPENAI_ORGANIZATION
#)

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_API_BASE
)

model = settings.OPENROUTER_MODEL
logger.info(f"Model loaded: {model}")
