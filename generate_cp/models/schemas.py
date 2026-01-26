from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional, Any

class CourseInformation(BaseModel):
    """Information about the course structure and organization"""
    course_title: str 
    name_of_organisation: str
    classroom_hours: int
    practical_hours: int
    number_of_assessment_hours: int
    course_duration: int
    industry: str

class LearningOutcomes(BaseModel):
    """Learning outcomes, knowledge and ability factors"""
    learning_outcomes: List[str]
    knowledge: List[str]  # Variable number of K factors
    ability: List[str]    # Variable number of A factors

class TSCAndTopics(BaseModel):
    """Training Standards Committee information and topics"""
    tsc_title: List[str]
    tsc_code: List[str]
    topics: List[str]      # Variable number of topics
    learning_units: List[str]  # Variable number of learning units

class TopicDetail(BaseModel):
    """Detailed information about a topic"""
    topic: str
    details: List[str]

class LearningUnitDescription(BaseModel):
    """Description of learning units with flexible structure"""
    description: List[Union[str, Dict[str, Any]]]

class CourseOutline(BaseModel):
    """Outline of the course with variable learning units"""
    learning_units: Dict[str, Union[LearningUnitDescription, List[str], Dict[str, Any]]]

class AssessmentMethods(BaseModel):
    """Assessment methods and related information"""
    assessment_methods: List[str]  # Variable assessment methods
    amount_of_practice_hours: str
    course_outline: CourseOutline
    instructional_methods: List[str]

class CourseEnsembleOutput(BaseModel):
    """Main output schema for the course ensemble"""
    course_information: CourseInformation = Field(..., alias="Course Information")
    learning_outcomes: LearningOutcomes = Field(..., alias="Learning Outcomes") 
    tsc_and_topics: TSCAndTopics = Field(..., alias="TSC and Topics")
    assessment_methods: AssessmentMethods = Field(..., alias="Assessment Methods")

    class Config:
        allow_population_by_field_name = True

# Assessment Justification Schema
class AssessmentEvidence(BaseModel):
    """Evidence for assessment with flexible structure"""
    evidence: Union[str, Dict[str, str], List[str]]

class AssessmentMethod(BaseModel):
    """Information about an assessment method"""
    name: str
    description: str
    focus: Optional[str] = None
    tasks: Optional[List[str]] = None
    evidence: Union[str, Dict[str, str], List[str]]
    submission: List[str]
    marking_process: List[str]
    retention_period: str
    no_of_scripts: Optional[str] = None

class AssessmentJustification(BaseModel):
    """Justification for assessment methods"""
    assessment_methods: Dict[str, AssessmentMethod]  # Dynamic assessment method names as keys

# Research Team Schema
class PerformanceAnalysis(BaseModel):
    """Analysis of performance gaps and benefits"""
    performance_gaps: List[str] = Field(..., alias="Performance Gaps")
    attributes_gained: List[str] = Field(..., alias="Attributes Gained")
    post_training_benefits: List[str] = Field(..., alias="Post-Training Benefits to Learners")

class LearningUnitAnalysis(BaseModel):
    """Analysis of a learning unit"""
    title: str = Field(..., alias="Title")
    description: str = Field(..., alias="Description")

class SequencingAnalysis(BaseModel):
    """Analysis of learning unit sequencing with variable number of LUs"""
    sequencing_explanation: str = Field(..., alias="Sequencing Explanation")
    lu1: LearningUnitAnalysis = Field(..., alias="LU1")
    lu2: LearningUnitAnalysis = Field(..., alias="LU2")
    lu3: Optional[LearningUnitAnalysis] = Field(None, alias="LU3")
    lu4: Optional[LearningUnitAnalysis] = Field(None, alias="LU4")
    lu5: Optional[LearningUnitAnalysis] = Field(None, alias="LU5")
    lu6: Optional[LearningUnitAnalysis] = Field(None, alias="LU6")
    conclusion: Optional[str] = Field(None, alias="Conclusion")

    # Allow for additional LUs with dynamic keys
    class Config:
        extra = "allow"

class BackgroundAnalysis(BaseModel):
    """Analysis of industry background and training needs"""
    industry_challenges: str = Field(..., alias="Challenges and performance gaps in the industry related to the course")
    training_needs: str = Field(..., alias="Training needs necessary to address these gaps")
    job_roles: str = Field(..., alias="Job roles that would benefit from the training")

class ResearchOutput(BaseModel):
    """Research team output"""
    background_analysis: BackgroundAnalysis = Field(..., alias="Background Analysis")
    performance_analysis: PerformanceAnalysis = Field(..., alias="Performance Analysis")
    sequencing_analysis: SequencingAnalysis = Field(..., alias="Sequencing Analysis")

    class Config:
        allow_population_by_field_name = True

# Excel Agent Schema
class DynamicContent(BaseModel):
    """Base model for dynamic content"""
    __root__: Dict[str, Any]

class CourseOverview(BaseModel):
    """Course overview information"""
    course_description: str

class ExcelData(BaseModel):
    """Excel agent output with dynamic sections"""
    course_overview: CourseOverview
    ka_analysis: Dict[str, str]  # Dynamic K&A factors
    instructional_methods: Optional[Dict[str, str]] = None  # Dynamic instructional methods
    
    # Allow for additional dynamic sections
    class Config:
        extra = "allow"