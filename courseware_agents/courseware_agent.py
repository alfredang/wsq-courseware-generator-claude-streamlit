"""
Courseware Agent

This agent handles generation of courseware documents:
- Assessment Plan (AP)
- Facilitator Guide (FG)
- Learner Guide (LG)
- Lesson Plan (LP)
- Timetable

Author: Courseware Generator Team
Date: 26 January 2026
"""

from agents import function_tool
from courseware_agents.base import create_agent
from courseware_agents.schemas import CoursewareAgentResponse, CoursewareDocument
import json


@function_tool
async def generate_assessment_plan(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Assessment Plan (AP) document from course data.

    Args:
        course_data_json: Course proposal data as JSON string
        organization_json: Organization details as JSON string
        model_choice: Model to use for generation

    Returns:
        Generated Assessment Plan data as JSON string
    """
    from generate_ap_fg_lg_lp.utils.agentic_AP import generate_assessment_documents

    course_data = json.loads(course_data_json)
    organization = json.loads(organization_json)

    result = await generate_assessment_documents(
        context=course_data,
        org_data=organization,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "data": result})


@function_tool
async def generate_facilitator_guide(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Facilitator Guide (FG) document.

    Args:
        course_data_json: Course proposal data as JSON string
        organization_json: Organization details as JSON string
        model_choice: Model to use for generation

    Returns:
        Generated Facilitator Guide data as JSON string
    """
    from generate_ap_fg_lg_lp.utils.agentic_FG import generate_facilitators_guide

    course_data = json.loads(course_data_json)
    organization = json.loads(organization_json)

    result = await generate_facilitators_guide(
        context=course_data,
        org_data=organization,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "data": result})


@function_tool
async def generate_learner_guide(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Learner Guide (LG) document.

    Args:
        course_data_json: Course proposal data as JSON string
        organization_json: Organization details as JSON string
        model_choice: Model to use for generation

    Returns:
        Generated Learner Guide data as JSON string
    """
    from generate_ap_fg_lg_lp.utils.agentic_LG import generate_learning_guide

    course_data = json.loads(course_data_json)
    organization = json.loads(organization_json)

    result = await generate_learning_guide(
        context=course_data,
        org_data=organization,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "data": result})


@function_tool
async def generate_lesson_plan(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "DeepSeek-Chat"
) -> str:
    """
    Generate Lesson Plan (LP) document.

    Args:
        course_data_json: Course proposal data as JSON string
        organization_json: Organization details as JSON string
        model_choice: Model to use for generation

    Returns:
        Generated Lesson Plan data as JSON string
    """
    from generate_ap_fg_lg_lp.utils.agentic_LP import generate_lesson_plan as gen_lp

    course_data = json.loads(course_data_json)
    organization = json.loads(organization_json)

    result = await gen_lp(
        context=course_data,
        org_data=organization,
        model_choice=model_choice
    )
    return json.dumps({"status": "success", "data": result})


@function_tool
def generate_timetable(
    course_data_json: str,
    start_date: str,
    organization_json: str
) -> str:
    """
    Generate course timetable.

    Args:
        course_data_json: Course proposal data as JSON string
        start_date: Course start date (YYYY-MM-DD)
        organization_json: Organization details as JSON string

    Returns:
        Generated timetable data as JSON string
    """
    from generate_ap_fg_lg_lp.utils.timetable_generator import generate_timetable as gen_tt

    course_data = json.loads(course_data_json)
    organization = json.loads(organization_json)

    result = gen_tt(
        context=course_data,
        start_date=start_date,
        org_data=organization
    )
    return json.dumps({"status": "success", "data": result})


# System instructions for the Courseware Agent
COURSEWARE_AGENT_INSTRUCTIONS = """You are the Courseware Agent, specialized in generating courseware documents from Course Proposal (CP) data.

## Document Types You Generate

1. **Assessment Plan (AP)** - Assessment criteria, marking schemes
2. **Facilitator Guide (FG)** - Teaching instructions, activity guidance
3. **Learner Guide (LG)** - Course content, exercises
4. **Lesson Plan (LP)** - Session breakdown, activities
5. **Timetable** - Course schedule

## Required Inputs

- **Course Data**: CP JSON data as a string
- **Organization**: Organization details as JSON string
- **Document Selection**: Which documents to generate

## Important Notes

- All data is passed as JSON strings
- Parse JSON strings before use
- Report progress after each document

## Example

User: "Generate a Facilitator Guide"
→ Request course_data_json and organization_json, then call generate_facilitator_guide
"""

# Create the Courseware Agent instance
courseware_agent = create_agent(
    name="Courseware Agent",
    instructions=COURSEWARE_AGENT_INSTRUCTIONS,
    tools=[
        generate_assessment_plan,
        generate_facilitator_guide,
        generate_learner_guide,
        generate_lesson_plan,
        generate_timetable,
    ],
    model_name="DeepSeek-Chat",
    handoff_description="Specialized agent for generating AP, FG, LG, LP courseware documents"
)
