"""
Entity Extraction Processor

This module handles entity extraction from documents and images using OpenRouter API.
Uses vision-capable models (GPT-4o, Gemini) for image processing.

Updated: 26 January 2026
"""

import os
import json
import base64
from typing import Dict, Any, Union
from PIL import Image
import io
from settings.api_manager import load_api_keys

# OpenAI client for OpenRouter
from openai import OpenAI

# Default model for entity extraction (vision-capable)
DEFAULT_MODEL = "openai/gpt-4o-mini"


def _get_openrouter_client() -> OpenAI:
    """Get OpenAI client configured for OpenRouter"""
    api_keys = load_api_keys()
    api_key = api_keys.get("OPENROUTER_API_KEY", "")

    if not api_key:
        api_key = api_keys.get("OPENAI_API_KEY", "")

    if not api_key:
        raise ValueError("No API key configured. Please set OPENROUTER_API_KEY in Settings.")

    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )


def extract_entities(document_content: Union[str, bytes], custom_instructions: str, is_image: bool = False) -> Dict[str, Any]:
    """
    Extract named entities from text or images using OpenRouter API.
    If `is_image` is True, process the content as an image.

    Args:
        document_content: Text content or image bytes
        custom_instructions: Additional instructions for extraction
        is_image: Whether the content is an image

    Returns:
        Dictionary with extracted entities
    """
    try:
        client = _get_openrouter_client()
    except ValueError as e:
        return {"error": str(e), "entities": []}

    # JSON format for response
    json_format = """
    {
        "entities": [
            {
                "type": "PERSON/COMPANY NAME/COMPANY UEN/DOCUMENT DATE/NRIC",
                "value": "extracted entity",
                "context": "relevant surrounding text"
            }
        ]
    }
    """

    system_prompt = f"""Task: Named Entity Extraction
Instructions: {custom_instructions}

Analyze the following document and extract named entities.
**STRICTLY return only JSON** in this format:
```json
{json_format}
```
Do not include any explanations, bullet points, or markdown formatting.
Exclude any mentions of Tertiary Infotech as the company."""

    try:
        # Handle image content
        if is_image and isinstance(document_content, bytes):
            # Convert bytes to base64 for API
            base64_image = base64.b64encode(document_content).decode('utf-8')

            # Use vision model for image processing
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": system_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
        elif isinstance(document_content, Image.Image):
            # Handle PIL Image objects
            buffer = io.BytesIO()
            document_content.save(buffer, format='PNG')
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": system_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
        else:
            # Handle text content
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": str(document_content)}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

        # Parse response
        response_text = response.choices[0].message.content.strip()

        # Clean up markdown if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse JSON
        extracted_entities = json.loads(response_text)

        # Validate structure
        if not isinstance(extracted_entities, dict) or "entities" not in extracted_entities:
            return {"entities": [], "error": "Invalid JSON format"}

        return extracted_entities

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {"entities": [], "error": "Invalid JSON response"}
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return {"entities": [], "error": str(e)}
