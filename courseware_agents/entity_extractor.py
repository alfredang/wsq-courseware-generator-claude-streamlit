"""
Entity Extraction Agent

Extracts named entities (names, companies, UEN, NRIC, dates)
from documents and images using the Claude Agent SDK.
"""

import json
import os
from courseware_agents.base import run_agent_json

SYSTEM_PROMPT = """You are an expert at extracting named entities from documents.

Extract the following entity types:
- PERSON: Full names of individuals
- COMPANY NAME: Company or organization names
- COMPANY UEN: Singapore Unique Entity Number (format: 20XXXXXXXXX)
- DOCUMENT DATE: Dates mentioned in the document
- NRIC: Masked NRIC numbers (format: SXXXX###X or similar)

CRITICAL: Return ONLY a valid JSON object with no additional text.

{
    "entities": [
        {
            "type": "PERSON|COMPANY NAME|COMPANY UEN|DOCUMENT DATE|NRIC",
            "value": "extracted value",
            "context": "surrounding text for verification"
        }
    ]
}

RULES:
1. Extract ALL instances of each entity type
2. For NRIC, preserve the masked format as-is
3. Exclude any mentions of "Tertiary Infotech" as the company
4. Include the surrounding context for each entity
5. If no entities found, return {"entities": []}
"""


async def extract_entities(
    document_text: str,
    custom_instructions: str = "",
) -> dict:
    """
    Extract named entities from document text.

    Args:
        document_text: The text content of the document.
        custom_instructions: Additional extraction instructions.

    Returns:
        Dict with 'entities' key containing extracted entities.
    """
    extra = ""
    if custom_instructions:
        extra = f"\n\nAdditional instructions: {custom_instructions}"

    prompt = f"""Extract all named entities from the following document text.
{extra}

--- DOCUMENT TEXT ---
{document_text}
--- END ---

Return ONLY the JSON object with the 'entities' key."""

    result = await run_agent_json(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        max_turns=5,
    )

    return result
