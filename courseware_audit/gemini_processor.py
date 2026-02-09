"""
Entity Extraction Processor

This module provides entity extraction from documents and images.
Entity extraction is handled by Claude Code skill (subscription-based).
No API tokens needed.

Updated: February 2026
"""

import json
from typing import Dict, Any, Union


def extract_entities(document_content: Union[str, bytes, Any], custom_instructions: str, is_image: bool = False) -> Dict[str, Any]:
    """
    Placeholder for entity extraction.

    Entity extraction is now handled by the Claude Code skill.
    This function returns a message directing users to use the skill.

    Args:
        document_content: Text content, image bytes, or PIL Image
        custom_instructions: Additional instructions for extraction
        is_image: Whether the content is an image

    Returns:
        Dictionary with empty entities and info message
    """
    return {
        "entities": [],
        "info": "Entity extraction is handled by Claude Code skill. "
                "Run `/courseware_audit` in Claude Code to extract entities from documents."
    }
