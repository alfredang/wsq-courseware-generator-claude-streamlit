import os
import json
from typing import Dict, Any, Union
from PIL import Image
import io
from settings.api_manager import load_api_keys

# Optional google.generativeai import
GENAI_AVAILABLE = False
model = None
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True

    # Configure API - load from settings
    api_keys = load_api_keys()
    GEMINI_API_KEY = api_keys.get("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-pro model with specific configuration
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
            },
        )
except ImportError:
    pass

def extract_entities(document_content: Union[str, bytes], custom_instructions: str, is_image: bool = False) -> Dict[str, Any]:
    """
    Extract named entities from text or images using Gemini API.
    If `is_image` is True, process the image as a PIL image.
    """
    if not GENAI_AVAILABLE or model is None:
        return {"error": "Gemini API not available. Please install google-generativeai package.", "entities": []}

    # Force Gemini to return valid JSON
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

    system_prompt = f"""
    Task: Named Entity Extraction
    Instructions: {custom_instructions}

    Analyze the following document and extract named entities.
    **STRICTLY return only JSON** in this format:
    ```json
    {json_format}
    ```
    Do not include any explanations, bullet points, or markdown formatting.
    Exclude any mentions of Tertiary Infotech as the company.
    """

    # Convert bytes to a PIL image before sending to Gemini
    if is_image and isinstance(document_content, bytes):
        image = Image.open(io.BytesIO(document_content))  # Convert bytes to image
        response = model.generate_content([system_prompt, image], stream=True)
    
    else:
        response = model.generate_content([system_prompt, document_content], stream=True)

    # Collect streamed response
    full_response = []
    for chunk in response:
        if chunk.text:
            cleaned_chunk = chunk.text.strip()

            # Ignore markdown artifacts (` ``` `, `json`)
            if cleaned_chunk in ["```", "json"]:
                continue
            
            print("Received chunk:", cleaned_chunk)  # Debugging output
            full_response.append(cleaned_chunk)

    # Join parts into a single response
    full_response_text = "".join(full_response).strip()

    # Remove enclosing triple backticks if present
    if full_response_text.startswith("```json"):
        full_response_text = full_response_text[7:]
    if full_response_text.endswith("```"):
        full_response_text = full_response_text[:-3]

    # Ensure the response starts with '{' and ends with '}'
    full_response_text = full_response_text.lstrip("json").strip()  # Remove leading 'json' if present

    if not full_response_text.startswith("{") or not full_response_text.endswith("}"):
        print(f"Malformed response detected:\n{full_response_text}")
        return {"entities": [], "error": "Malformed JSON from Gemini"}

    # Validate JSON structure
    try:
        extracted_entities = json.loads(full_response_text)

        # Ensure correct structure
        if not isinstance(extracted_entities, dict) or "entities" not in extracted_entities:
            print(f"Invalid response structure: {full_response_text}")
            return {"entities": [], "error": "Invalid JSON format"}

        return extracted_entities

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {full_response_text}")
        return {"entities": [], "error": "Invalid JSON response from Gemini"}
