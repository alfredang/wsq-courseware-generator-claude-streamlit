"""
Courseware Audit Agent

Extracts audit fields from courseware documents (AP, FG, LG, LP)
for cross-document consistency checking.

ALL audit rules and check items are defined in:
  courseware_agents/audit/templates/audit_extraction.md

The Python code is a thin wrapper — no hardcoded rules.
"""

import os
import re
import asyncio
import threading
from courseware_agents.base import run_agent_json

# Path to the template file (single source of truth)
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
_TEMPLATE_FILE = os.path.join(_TEMPLATE_DIR, "audit_extraction.md")

# Cache
_PARSED_TEMPLATE = None


def _load_template() -> str:
    """Load the raw template content.

    Priority:
      1. Database template (if it has the new ## Audit Check Items format)
      2. File template: courseware_agents/audit/templates/audit_extraction.md
    """
    # Try editable database template first
    try:
        from settings.api_database import get_prompt_template
        template = get_prompt_template("courseware_audit", "audit_extraction")
        if template and template.get("content"):
            content = template["content"]
            # Only use DB template if it has the structured format
            if "## Audit Check Items" in content and "## System Prompt" in content:
                return content
    except Exception:
        pass

    # Fall back to the .md template file (single source of truth)
    with open(_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _parse_template():
    """Parse the .md template to extract audit checks and system prompt.

    Returns dict with:
      - "checks": list of (display_name, field_key, field_type, applicable_types)
      - "system_prompt": the system prompt text for the AI agent
    """
    global _PARSED_TEMPLATE
    # Always reload to pick up template changes without restart
    _PARSED_TEMPLATE = None

    content = _load_template()

    # Parse the audit checks table
    checks = []
    in_table = False
    for line in content.split("\n"):
        line = line.strip()
        # Skip header separator row
        if line.startswith("|---") or line.startswith("| Display Name"):
            in_table = True
            continue
        if in_table and line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 4:
                display_name = cells[0]
                field_key = cells[1]
                field_type = cells[2]
                applicable = cells[3].strip()
                applicable_types = None if applicable.lower() == "all" else [
                    t.strip() for t in applicable.split(",")
                ]
                checks.append((display_name, field_key, field_type, applicable_types))
        elif in_table and not line.startswith("|"):
            in_table = False

    # Parse system prompt — everything after "## System Prompt" until next "##"
    system_prompt = ""
    match = re.search(
        r'## System Prompt\s*\n(.*?)(?=\n## |\Z)',
        content,
        re.DOTALL,
    )
    if match:
        system_prompt = match.group(1).strip()

    # Append extraction rules if present
    rules_match = re.search(
        r'## Extraction Rules\s*\n(.*?)(?=\n## |\Z)',
        content,
        re.DOTALL,
    )
    if rules_match:
        system_prompt += "\n\nRULES:\n" + rules_match.group(1).strip()

    _PARSED_TEMPLATE = {
        "checks": checks,
        "system_prompt": system_prompt,
    }
    return _PARSED_TEMPLATE


def get_audit_checks() -> list[tuple]:
    """Get audit check items from the template.

    Returns list of (display_name, field_key, field_type, applicable_types).
    This is used by the UI (sup_doc.py) to render checkboxes.
    """
    parsed = _parse_template()
    return parsed["checks"]


def get_system_prompt() -> str:
    """Get the system prompt for the audit agent."""
    parsed = _parse_template()
    return parsed["system_prompt"]


async def _extract_async(document_text: str, document_type: str) -> dict:
    """Internal async extraction using Claude Agent SDK."""
    type_hint = f"\nThis document is a {document_type}." if document_type else ""

    # Truncate very large documents to avoid token limits
    max_chars = 80000
    if len(document_text) > max_chars:
        document_text = document_text[:max_chars] + "\n... [truncated]"

    prompt = f"""Extract all audit fields from the following courseware document.{type_hint}

--- DOCUMENT CONTENT ---
{document_text}
--- END ---

Return ONLY the JSON object with all extracted fields."""

    system_prompt = get_system_prompt()

    result = await run_agent_json(
        prompt=prompt,
        system_prompt=system_prompt,
        tools=[],
        max_turns=5,
    )

    return result


def extract_audit_fields(document_text: str, document_type: str = "") -> dict:
    """
    Extract audit fields from a courseware document using Claude Agent SDK.

    Handles Streamlit's event loop by running async code in a separate thread.

    Args:
        document_text: The full text content of the document.
        document_type: The type of document (CP, AP, FG, LG, LP) for context.

    Returns:
        Dict with extracted audit fields.
    """
    result = [None]
    error = [None]

    def _run_in_thread():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result[0] = loop.run_until_complete(_extract_async(document_text, document_type))
            loop.close()
        except Exception as e:
            error[0] = e

    thread = threading.Thread(target=_run_in_thread)
    thread.start()
    thread.join()

    if error[0]:
        raise error[0]
    return result[0]
