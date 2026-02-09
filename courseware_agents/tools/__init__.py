"""
Courseware Tools Module

This module contains all tool implementations for the courseware agents.
Tools are exposed via MCP server for Claude Agent SDK integration.

Author: Courseware Generator Team
Date: 26 January 2026
"""

# Courseware Agent Tools
from courseware_agents.tools.courseware_tools import (
    generate_assessment_plan,
    generate_facilitator_guide,
    generate_learner_guide,
    generate_lesson_plan,
    generate_timetable,
)

# Assessment Agent Tools
from courseware_agents.tools.assessment_tools import (
    generate_saq_questions,
    generate_practical_performance,
    generate_case_study,
    parse_facilitator_guide,
    interpret_fg_content,
)

# Brochure Agent Tools
from courseware_agents.tools.brochure_tools import (
    scrape_course_info,
    generate_brochure_html,
    generate_brochure_pdf,
    create_brochure_from_cp,
    generate_marketing_content,
)

# Document Agent Tools
from courseware_agents.tools.document_tools import (
    extract_document_entities,
    verify_against_training_records,
    verify_company_uen,
    check_document_completeness,
)

__all__ = [
    # Courseware Tools
    "generate_assessment_plan",
    "generate_facilitator_guide",
    "generate_learner_guide",
    "generate_lesson_plan",
    "generate_timetable",
    # Assessment Tools
    "generate_saq_questions",
    "generate_practical_performance",
    "generate_case_study",
    "parse_facilitator_guide",
    "interpret_fg_content",
    # Brochure Tools
    "scrape_course_info",
    "generate_brochure_html",
    "generate_brochure_pdf",
    "create_brochure_from_cp",
    "generate_marketing_content",
    # Document Tools
    "extract_document_entities",
    "verify_against_training_records",
    "verify_company_uen",
    "check_document_completeness",
]
