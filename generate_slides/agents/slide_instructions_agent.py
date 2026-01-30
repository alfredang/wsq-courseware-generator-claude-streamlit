"""
Slide Instructions Agent for Slides Generation.

Crafts optimal NotebookLM instructions instead of using hardcoded strings.
Analyzes the document structure, topics, and learning outcomes to generate
tailored instructions for the best possible slide deck.

Uses JSON mode for structured output via OpenRouter-compatible models.
"""

import json
import logging
from typing import Dict, Any, List

from generate_cp.utils.openai_model_client import create_openai_client
from utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str) -> dict:
    """
    Extract JSON from a response string, handling markdown code blocks.

    Args:
        content: The response content that may contain JSON

    Returns:
        Parsed JSON dictionary
    """
    if content is None:
        return {}

    if "```json" in content:
        start = content.find("```json") + 7
        end = content.find("```", start)
        if end != -1:
            content = content[start:end].strip()
    elif "```" in content:
        start = content.find("```") + 3
        end = content.find("```", start)
        if end != -1:
            content = content[start:end].strip()

    if "{" in content:
        start = content.find("{")
        depth = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from slide instructions response")
        return {}


async def run_slide_instructions(
    content: str,
    topics: List[Dict[str, Any]],
    config: Dict[str, Any],
    research_sources_count: int,
    model_choice: str,
) -> Dict[str, Any]:
    """
    Generate optimal NotebookLM slide generation instructions.

    Args:
        content: Document content (truncated for summary)
        topics: List of topic dicts from topic analysis agent
        config: Slide configuration from UI (style, notes, summaries etc.)
        research_sources_count: Number of approved research sources
        model_choice: Model selection string for create_openai_client

    Returns:
        Dict with 'instructions' (string for NotebookLM),
        'estimated_slides', 'structure_outline'
    """
    client, model_config = create_openai_client(model_choice)

    # Build document summary (first 5000 chars)
    document_summary = content[:5000]

    # Build topics list string
    topics_list = "\n".join(
        f"- {t.get('name', 'Unknown')}: {t.get('rationale', '')}"
        for t in topics
    ) if topics else "No specific topics identified."

    system_message = load_prompt(
        "slides/slide_instructions",
        material_type=config.get("material_type", "Course Material"),
        slide_style=config.get("slide_style", "Professional"),
        slides_per_topic=config.get("slides_per_topic", 3),
        include_notes=str(config.get("include_notes", True)),
        include_summaries=str(config.get("include_summaries", True)),
        include_objectives=str(config.get("include_objectives", True)),
        include_assessment=str(config.get("include_assessment", True)),
        has_research_sources=str(research_sources_count > 0),
        research_sources_count=research_sources_count,
        document_summary=document_summary,
        topics_list=topics_list,
    )

    user_task = (
        "Generate the optimal slide generation instructions based on the analysis above. "
        "Return as JSON."
    )

    logger.info(f"Running slide instructions agent with {len(topics)} topics, "
                f"{research_sources_count} research sources")

    completion = client.chat.completions.create(
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=4000,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_task},
        ],
        response_format={"type": "json_object"},
    )

    result = extract_json_from_response(completion.choices[0].message.content)

    instructions = result.get("instructions", "")
    logger.info(f"Slide instructions generated: {len(instructions)} chars, "
                f"estimated {result.get('estimated_slides', 'N/A')} slides")

    return result
