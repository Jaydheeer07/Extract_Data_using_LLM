from openai import OpenAI   
from app.config import settings

client = OpenAI(
    api_key=settings.OPENAI_API_KEY, organization=settings.OPENAI_ORGANIZATION
)
