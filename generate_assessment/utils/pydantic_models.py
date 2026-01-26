"""
File: pydantic_models.py

===============================================================================
Pydantic Models for Facilitator Guide Extraction and WSQ Structured Output
===============================================================================
Description:
    This module defines a set of Pydantic models used for validating and structuring data
    extracted from a Facilitator Guide for courseware assessments. The models encapsulate
    essential elements such as Knowledge Statements, Ability Statements, Topics, Learning Units,
    and Assessment Methods. Additionally, specialized models are provided to structure outputs
    for case study questions and WSQ (Workforce Skills Qualifications) assessments.

Main Functionalities:
    • KnowledgeStatement, AbilityStatement, and Topic:
          Define the core components for representing course content, including the text and
          identifiers for knowledge and ability statements, along with associated topics.
    • LearningUnit and FacilitatorGuideExtraction:
          Structure the overall course data including learning outcomes and assessment methods.
    • CaseStudyQuestion and CaseStudy:
          Represent a case study scenario and its corresponding question-answer pairs.
    • WSQ:
          Specifies the model for generating structured WSQ assessment output.
    • LearningOutcomeContent:
          Represents the retrieved content for each Knowledge Statement linked to a learning outcome.

Dependencies:
    - Pydantic: Provides robust data validation and model creation.
    - Typing: Offers type annotations for lists and other complex data structures.

Usage:
    - Import the desired model from this module to validate and manipulate data extracted from
      the Facilitator Guide.
      Example:
          from pydantic_models import FacilitatorGuideExtraction
          fg_data = FacilitatorGuideExtraction(**data)

Author:
    Derrick Lim
Date:
    3 March 2025
===============================================================================
"""

from pydantic import BaseModel, Field
from typing import List

class KnowledgeStatement(BaseModel):
    id: str
    text: str


class AbilityStatement(BaseModel):
    id: str
    text: str


class Topic(BaseModel):
    name: str
    subtopics: List[str]
    tsc_knowledges: List[KnowledgeStatement]
    tsc_abilities: List[AbilityStatement]


class LearningUnit(BaseModel):
    name: str
    topics: List[Topic]
    learning_outcome: str


class AssessmentMethod(BaseModel):
    code: str
    duration: str
    
class FacilitatorGuideExtraction(BaseModel):
    course_title: str
    tsc_proficiency_level: str
    learning_units: List[LearningUnit]
    assessments: List[AssessmentMethod]

class CaseStudyQuestion(BaseModel):
    question: str
    answer: str
    ability_id: List[str]

class CaseStudy(BaseModel):
    scenario: str
    questions: List[CaseStudyQuestion]

# Define the WSQ model for structured output
class WSQ(BaseModel):
    knowledge_id: str = Field(..., description="The ID of the Knowledge Statement, e.g., K1, K2.")
    knowledge_statement: str = Field(..., description="The text of the Knowledge Statement.")
    scenario: str = Field(..., description="The realistic workplace scenario.")
    question: str = Field(..., description="The question based on the scenario.")
    answer: str = Field(..., description="The concise answer to the question.")

class LearningOutcomeContent(BaseModel):
    ability_id: List[str]
    retrieved_content: str = Field(..., description="The content retrieved for this Knowledge Statement.")