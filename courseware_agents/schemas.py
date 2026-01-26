"""
Pydantic Schemas for Courseware Agents

This module provides structured output types for the multi-agent system.
It imports existing schemas and defines new ones for agent responses.

Author: Courseware Generator Team
Date: 26 January 2026
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union


# =============================================================================
# Import existing schemas from other modules
# =============================================================================

# Course Proposal schemas
from generate_cp.models.schemas import (
    CourseInformation,
    LearningOutcomes,
    TSCAndTopics,
    AssessmentMethods,
    CourseEnsembleOutput,
    AssessmentJustification,
)

# Assessment schemas
from generate_assessment.utils.pydantic_models import (
    FacilitatorGuideExtraction,
    LearningUnit,
    Topic,
    KnowledgeStatement,
    AbilityStatement,
)


# =============================================================================
# Agent Response Schemas
# =============================================================================

class CPAgentResponse(BaseModel):
    """Structured response from CP Agent"""
    status: str = Field(description="success or error")
    course_data: Optional[CourseEnsembleOutput] = Field(
        default=None,
        description="Extracted course proposal data"
    )
    document_path: Optional[str] = Field(
        default=None,
        description="Path to generated document"
    )
    message: str = Field(description="Status message or error details")


class CoursewareDocument(BaseModel):
    """Generated courseware document info"""
    document_type: str = Field(description="AP, FG, LG, or LP")
    status: str = Field(description="success or error")
    content: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generated document content"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Path to saved document"
    )


class CoursewareAgentResponse(BaseModel):
    """Structured response from Courseware Agent"""
    status: str = Field(description="success or error")
    documents: List[CoursewareDocument] = Field(
        default_factory=list,
        description="List of generated documents"
    )
    message: str = Field(description="Status message")


class SAQQuestion(BaseModel):
    """Short Answer Question structure"""
    question_number: int
    question: str
    model_answer: str
    marks: int = Field(default=2)
    learning_outcome: Optional[str] = None


class PracticalPerformance(BaseModel):
    """Practical Performance assessment structure"""
    task_title: str
    task_description: str
    performance_criteria: List[str]
    materials_required: List[str] = Field(default_factory=list)
    time_allowed: Optional[str] = None


class CaseStudyScenario(BaseModel):
    """Case Study assessment structure"""
    scenario_title: str
    scenario_description: str
    questions: List[Dict[str, str]] = Field(
        description="List of questions with model answers"
    )
    learning_outcomes_covered: List[str] = Field(default_factory=list)


class AssessmentAgentResponse(BaseModel):
    """Structured response from Assessment Agent"""
    status: str = Field(description="success or error")
    assessment_type: str = Field(description="SAQ, PP, or CS")
    saq_questions: Optional[List[SAQQuestion]] = None
    practical_performance: Optional[PracticalPerformance] = None
    case_study: Optional[CaseStudyScenario] = None
    message: str = Field(description="Status message")


class BrochureContent(BaseModel):
    """Marketing brochure content structure"""
    course_title: str
    tagline: Optional[str] = None
    course_description: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    duration: Optional[str] = None
    certification: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    call_to_action: Optional[str] = None


class BrochureAgentResponse(BaseModel):
    """Structured response from Brochure Agent"""
    status: str = Field(description="success or error")
    brochure_data: Optional[BrochureContent] = None
    html_content: Optional[str] = Field(
        default=None,
        description="Generated HTML brochure"
    )
    pdf_path: Optional[str] = Field(
        default=None,
        description="Path to generated PDF"
    )
    message: str = Field(description="Status message")


class ExtractedEntity(BaseModel):
    """Entity extracted from document"""
    entity_type: str = Field(
        description="PERSON, COMPANY NAME, COMPANY UEN, DOCUMENT DATE, NRIC"
    )
    value: str = Field(description="Extracted entity value")
    context: Optional[str] = Field(
        default=None,
        description="Surrounding text context"
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score 0-1"
    )


class DocumentVerification(BaseModel):
    """Document verification result"""
    document_name: str
    is_valid: bool
    entities: List[ExtractedEntity] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class DocumentAgentResponse(BaseModel):
    """Structured response from Document Agent"""
    status: str = Field(description="success or error")
    verifications: List[DocumentVerification] = Field(default_factory=list)
    uen_valid: Optional[bool] = Field(
        default=None,
        description="UEN validation result"
    )
    completeness_score: Optional[float] = Field(
        default=None,
        description="Document completeness 0-100"
    )
    message: str = Field(description="Status message")


class OrchestratorResponse(BaseModel):
    """Structured response from Orchestrator"""
    response: str = Field(description="Response message to user")
    agent_used: Optional[str] = Field(
        default=None,
        description="Name of specialized agent used"
    )
    action_taken: Optional[str] = Field(
        default=None,
        description="Action performed"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Suggested next steps for user"
    )


# =============================================================================
# Export all schemas
# =============================================================================

__all__ = [
    # Imported schemas
    "CourseInformation",
    "LearningOutcomes",
    "TSCAndTopics",
    "AssessmentMethods",
    "CourseEnsembleOutput",
    "AssessmentJustification",
    "FacilitatorGuideExtraction",
    "LearningUnit",
    "Topic",
    "KnowledgeStatement",
    "AbilityStatement",
    # Agent response schemas
    "CPAgentResponse",
    "CoursewareDocument",
    "CoursewareAgentResponse",
    "SAQQuestion",
    "PracticalPerformance",
    "CaseStudyScenario",
    "AssessmentAgentResponse",
    "BrochureContent",
    "BrochureAgentResponse",
    "ExtractedEntity",
    "DocumentVerification",
    "DocumentAgentResponse",
    "OrchestratorResponse",
]
