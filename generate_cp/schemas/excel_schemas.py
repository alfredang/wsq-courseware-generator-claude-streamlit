"""
Pydantic schemas for Excel agent structured outputs.

This module defines the data models used for validating and parsing
JSON outputs from the OpenAI-based Excel agents.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

from pydantic import BaseModel, Field
from typing import Dict


class CourseOverviewSchema(BaseModel):
    """Schema for course overview/description output."""
    course_description: str = Field(
        ...,
        description="Course description in 2 paragraphs (max 300 words)"
    )


class CourseOverviewResponse(BaseModel):
    """Top-level response schema for course agent."""
    course_overview: CourseOverviewSchema


class KAAnalysisResponse(BaseModel):
    """
    Schema for Knowledge and Ability (K&A) analysis output.

    The keys are dynamic (K1, K2, A1, A2, etc.) based on the K&A factors
    present in the course data. Each value is a max 50-word explanation.
    """
    KA_Analysis: Dict[str, str] = Field(
        ...,
        description="Dictionary mapping K/A factor codes (K1, K2, A1, etc.) to explanations"
    )


class InstructionalMethodsResponse(BaseModel):
    """
    Schema for instructional methods analysis output.

    The keys are instructional method names (e.g., "Lecture", "Didactic Questioning")
    and values are contextualised explanations for each method.
    """
    Instructional_Methods: Dict[str, str] = Field(
        ...,
        description="Dictionary mapping instructional method names to contextualised explanations"
    )
