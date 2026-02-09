"""
Courseware Audit Agent

Extracts audit fields from courseware documents (AP, FG, LG, LP)
for cross-document consistency checking.
"""

from courseware_agents.base import run_agent_json

SYSTEM_PROMPT = """You are a WSQ courseware document auditor.

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
    "learning_outcomes": [
        "string - LO1: description",
        "string - LO2: description"
    ],
    "durations": {
        "training_hours": "string or null - e.g., '16 hrs'",
        "assessment_hours": "string or null - e.g., '2 hrs'",
        "total_hours": "string or null - e.g., '18 hrs'"
    },
    "topics": [
        "string - Topic title 1",
        "string - Topic title 2"
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
- For assessment methods, include both the full name and abbreviation if available
- For topics, list all unique topic titles found
- For durations, extract all three if available (training, assessment, total)
- Return empty arrays [] if no items found for list fields
- Be thorough - scan the entire document content
"""


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

    result = await run_agent_json(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        max_turns=5,
    )

    return result
