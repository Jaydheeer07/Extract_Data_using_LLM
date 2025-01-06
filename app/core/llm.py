import base64
import json
import logging
from io import BytesIO

from openai import OpenAI

from app.config import settings
from app.core.prompt import extract_prompt
from app.model.extracted_model import InvoiceInfo

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(
    api_key=settings.OPENAI_API_KEY, organization=settings.OPENAI_ORGANIZATION
)


def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def extract_info(image):
    try:
        base64_image = encode_image_to_base64(image)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": extract_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.75,
            max_completion_tokens=4096,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        # Log token usage
        token_usage = response.usage
        logger.info(
            "Token usage: prompt_tokens=%d, completion_tokens=%d, total_tokens=%d",
            token_usage.prompt_tokens,
            token_usage.completion_tokens,
            token_usage.total_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("Error in extract_info: %s", str(e))
        raise


def parse_and_validate_llm_output(output):
    try:
        # Parse the JSON output from the LLM
        data = json.loads(output)
        # Validate and parse using the Pydantic model
        return InvoiceInfo(**data)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM output as JSON: %s", str(e))
        return {"error": "Invalid JSON output from LLM"}
    except Exception as e:
        logger.error("Failed to validate LLM output: %s", str(e))
        return {"error": "Invalid data structure in LLM output"}
