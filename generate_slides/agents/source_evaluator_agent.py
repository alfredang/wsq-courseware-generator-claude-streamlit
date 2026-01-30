"""
Source Quality Evaluator Agent for Slides Generation.

Evaluates research sources for relevance and quality before importing
them into the NotebookLM notebook. Filters out low-quality or
irrelevant sources to improve slide content.

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
        logger.warning("Failed to parse JSON from source evaluator response")
        return {}


async def run_source_evaluator(
    sources: List[Dict[str, str]],
    document_domain: str,
    research_query: str,
    material_type: str,
    model_choice: str,
) -> Dict[str, Any]:
    """
    Evaluate and filter research sources by quality.

    Called once per research query batch (not per source) to minimize LLM calls.

    Args:
        sources: List of dicts with 'url', 'title', and optionally 'summary' keys
        document_domain: Domain identified by topic analysis agent
        research_query: The research query that found these sources
        material_type: Document type (FG, LG, CP)
        model_choice: Model selection string for create_openai_client

    Returns:
        Dict with evaluated_sources (each with scores and approved flag),
        approved_count, rejected_count
    """
    client, config = create_openai_client(model_choice)

    system_message = load_prompt(
        "slides/source_evaluation",
        document_domain=document_domain,
        research_query=research_query,
        material_type=material_type,
    )

    sources_text = json.dumps(sources, indent=2)

    user_task = (
        f"Evaluate the following {len(sources)} research sources:\n\n"
        f"{sources_text}\n\n"
        f"Return your evaluation as a JSON object."
    )

    logger.info(f"Running source evaluator agent: {len(sources)} sources for query '{research_query[:60]}'")

    completion = client.chat.completions.create(
        model=config["model"],
        temperature=config["temperature"],
        max_tokens=4000,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_task},
        ],
        response_format={"type": "json_object"},
    )

    result = extract_json_from_response(completion.choices[0].message.content)

    approved = sum(1 for s in result.get("evaluated_sources", []) if s.get("approved", False))
    rejected = len(result.get("evaluated_sources", [])) - approved
    logger.info(f"Source evaluation complete: {approved} approved, {rejected} rejected")

    return result
