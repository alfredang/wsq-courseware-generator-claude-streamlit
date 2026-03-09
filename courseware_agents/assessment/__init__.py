"""
Assessment Generation Agent

Generates WSQ assessment questions (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ)
from course context and K/A statements.

Tools: None (all data passed via prompt)
Model: claude-sonnet-4-20250514 (default)
Called by: generate_assessment/assessment_generation.py
"""

from courseware_agents.assessment.assessment_generator import (
    generate_assessments,
)

__all__ = [
    "generate_assessments",
]
