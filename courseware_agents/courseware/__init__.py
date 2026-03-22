"""Courseware document generators (AP, FG, LG).

Pure Python template filling using docxtpl — takes structured context
from cp_interpreter and generates DOCX documents.
"""

from courseware_agents.courseware.assessment_plan import (
    generate_assessment_plan,
    generate_asr_document,
    generate_assessment_documents,
)
from courseware_agents.courseware.facilitator_guide import generate_facilitators_guide
from courseware_agents.courseware.learner_guide import generate_learning_guide

__all__ = [
    "generate_assessment_plan",
    "generate_asr_document",
    "generate_assessment_documents",
    "generate_facilitators_guide",
    "generate_learning_guide",
]
