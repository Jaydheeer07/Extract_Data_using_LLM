import base64
import json
import logging
from io import BytesIO

from app.core.client import client, get_current_model
from app.config import settings
from app.core.prompt import extract_prompt
from app.model.extracted_model import InvoiceInfo

logger = logging.getLogger(__name__)


def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def extract_info(image):
    try:
        # Get the current model from session state or settings
        current_model = get_current_model()
        logger.info(f"Using model for extraction: {current_model}")
        
        base64_image = encode_image_to_base64(image)
        response = client.chat.completions.create(
            model=current_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts information from documents. Always respond with valid JSON that matches the required schema. Include all required fields and format dates as YYYY-MM-DD."
                },
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
            temperature=0.75,
            max_tokens=4096,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        # Log the full response for debugging
        logger.info(f"OpenRouter raw response: {response}")
        logger.info(f"Response type: {type(response)}")
        
        if response is None:
            logger.error("OpenRouter API returned None")
            return None

        if not hasattr(response, 'choices') or not response.choices:
            logger.error(f"OpenRouter API response missing choices: {response}")
            return None

        # Log the message content
        message_content = response.choices[0].message.content
        logger.info(f"Message content: {message_content}")
        logger.info(f"Message content type: {type(message_content)}")

        # OpenRouter might not include usage information
        if hasattr(response, 'usage') and response.usage:
            logger.info(f"Token usage: prompt_tokens={getattr(response.usage, 'prompt_tokens', 'N/A')}, completion_tokens={getattr(response.usage, 'completion_tokens', 'N/A')}, total_tokens={getattr(response.usage, 'total_tokens', 'N/A')}")
        
        return message_content
    except Exception as e:
        logger.error(f"Error in extract_info: {str(e)}")
        return None


def parse_and_validate_llm_output(output):
    try:
        if output is None:
            logger.error("LLM output is None")
            return {"error": "No output from LLM"}
            
        if not isinstance(output, (str, bytes, bytearray)):
            logger.error(f"Unexpected output type: {type(output)}")
            return {"error": f"Unexpected output type: {type(output)}"}
        
        # Remove markdown code block if present
        if output.startswith('```') and output.endswith('```'):
            # Split by newline and remove first and last lines (```json and ```)
            lines = output.split('\n')[1:-1]
            output = '\n'.join(lines)
        
        # Parse the JSON output from the LLM
        data = json.loads(output)
        logger.info(f"Parsed JSON data: {data}")
        
        # Validate and parse using the Pydantic model
        result = InvoiceInfo(**data)
        return result
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM output as JSON: %s", str(e))
        logger.error(f"Raw output: {output}")
        return {"error": "Invalid JSON output from LLM"}
    except Exception as e:
        logger.error("Failed to validate LLM output: %s", str(e))
        logger.error(f"Data causing error: {output}")
        return {"error": "Invalid data structure in LLM output"}
