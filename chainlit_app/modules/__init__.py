"""
Chainlit Modules for WSQ Courseware Generator

Each module handles a specific workflow:
- course_proposal: Generate Course Proposals from TSC documents
- courseware: Generate AP/FG/LG/LP documents
- assessment: Generate 9 types of assessments
- slides: Generate presentation slides via NotebookLM
- brochure: Generate course brochures
- annex_assessment: Add assessments to AP documents
- check_documents: Verify supporting documents
- settings: Configure API keys, models, and preferences
"""

from . import course_proposal
from . import courseware
from . import assessment
from . import slides
from . import brochure
from . import annex_assessment
from . import check_documents
from . import settings

__all__ = [
    "course_proposal",
    "courseware",
    "assessment",
    "slides",
    "brochure",
    "annex_assessment",
    "check_documents",
    "settings",
]
