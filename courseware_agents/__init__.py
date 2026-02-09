"""
Courseware Agents Module

Provides agentic AI capabilities using the Claude Agent SDK.
Each agent specializes in a specific courseware generation task.

Agents:
- CP Interpreter: Extracts structured course data from Course Proposals
- Assessment Generator: Generates assessment questions from Facilitator Guides
- Timetable Generator: Creates lesson plan timetables
- Entity Extractor: Extracts named entities from documents
- Slides Agent: AI-enhanced slide generation analysis
"""

from courseware_agents.base import run_agent
from courseware_agents.cp_interpreter import interpret_cp
from courseware_agents.assessment_generator import generate_assessments
from courseware_agents.timetable_agent import generate_timetable
from courseware_agents.entity_extractor import extract_entities
from courseware_agents.slides_agent import analyze_document_for_slides

__all__ = [
    "run_agent",
    "interpret_cp",
    "generate_assessments",
    "generate_timetable",
    "extract_entities",
    "analyze_document_for_slides",
]
