"""
Courseware Audit Agent

Extracts key fields from AP/FG/LG/LP documents for cross-document
consistency checking (TGS codes, course titles, durations, topics, etc.).

Tools: None (document text passed via prompt)
Model: claude-sonnet-4-20250514 (default)
Called by: courseware_audit/sup_doc.py
"""

from courseware_agents.audit.audit_agent import (
    extract_audit_fields,
)

__all__ = [
    "extract_audit_fields",
]
