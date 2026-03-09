"""
Courseware Audit Agent

Extracts audit fields from courseware documents (AP, FG, LG, LP)
for cross-document consistency checking.

The system prompt is loaded from the editable prompt template database
(category: courseware_audit, name: audit_extraction). Falls back to a
hardcoded default if the template is not found.
"""

from courseware_agents.base import run_agent_json

DEFAULT_SYSTEM_PROMPT = """You are a WSQ courseware document auditor.

Your task is to extract specific fields from a courseware document for audit purposes.
The document may be an Assessment Plan (AP), Facilitator Guide (FG), Learner Guide (LG),
or Lesson Plan (LP).

Extract ALL of the following fields. If a field is not found, use null.

CRITICAL: Return ONLY a valid JSON object with no additional text.

The JSON must follow this schema:
{
    "tgs_ref_code": "string or null - TGS Reference Code (e.g., TGS-2024-12345)",
    "course_title": "string or null - Full course title",
    "company_name": "string or null - Training provider / company name",
    "tsc_ref_code": "string or null - Technical Skills & Competency code (e.g., ICT-DIT-3001-1.1)",
    "tsc_title": "string or null - TSC title / competency name",
    "num_lus": "integer - Total number of Learning Units found in the document",
    "learning_outcomes": [
        "string - LO1: description",
        "string - LO2: description"
    ],
    "lu_structure": [
        {
            "lu_number": 1,
            "lo": "string - Learning outcome for this LU",
            "topic_count": 3,
            "topic_titles": ["Topic 1 title", "Topic 2 title", "Topic 3 title"]
        },
        {
            "lu_number": 2,
            "lo": "string - Learning outcome for this LU",
            "topic_count": 2,
            "topic_titles": ["Topic 1 title", "Topic 2 title"]
        }
    ],
    "durations": {
        "training_hours": "string or null - e.g., '16 hrs'",
        "assessment_hours": "string or null - e.g., '2 hrs'",
        "total_hours": "string or null - e.g., '18 hrs'"
    },
    "topics": [
        "string - All topic titles across all LUs, in order"
    ],
    "assessment_methods": [
        "string - e.g., Written Assessment - Short Answer Questions (WA-SAQ)",
        "string - e.g., Practical Performance (PP)"
    ],
    "instructional_methods": [
        "string - e.g., Lecture",
        "string - e.g., Group Discussion"
    ]
}

RULES:
- Extract the EXACT values as they appear in the document
- For learning outcomes, include the LO number prefix (LO1, LO2, etc.)
- For lu_structure, group topics under their respective Learning Unit
- num_lus should be the total count of distinct Learning Units
- For assessment methods, include both the full name and abbreviation if available
- For topics, list ALL topic titles found across all LUs in order
- For durations, extract all three if available (training, assessment, total)
- Return empty arrays [] if no items found for list fields
- Be thorough - scan the entire document content
"""


def _get_system_prompt() -> str:
    """Load the audit extraction prompt from the template database, with fallback."""
    try:
        from settings.api_database import get_prompt_template
        template = get_prompt_template("courseware_audit", "audit_extraction")
        if template and template.get("content"):
            return template["content"]
    except Exception:
        pass
    return DEFAULT_SYSTEM_PROMPT


async def extract_audit_fields(document_text: str, document_type: str = "") -> dict:
    """
    Extract audit fields from a courseware document.

    Args:
        document_text: The full text content of the document.
        document_type: The type of document (AP, FG, LG, LP) for context.

    Returns:
        Dict with extracted audit fields.
    """
    type_hint = f"\nThis document is a {document_type}." if document_type else ""

    prompt = f"""Extract all audit fields from the following courseware document.{type_hint}

--- DOCUMENT CONTENT ---
{document_text}
--- END ---

Return ONLY the JSON object with all extracted fields."""

    system_prompt = _get_system_prompt()

    result = await run_agent_json(
        prompt=prompt,
        system_prompt=system_prompt,
        tools=[],
        max_turns=5,
    )

    return result
