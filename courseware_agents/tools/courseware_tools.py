"""
Courseware Tools

Tool implementations for Courseware Agent - AP/FG/LG/LP document generation.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import json


async def generate_assessment_plan(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "claude-sonnet-4"
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


async def generate_facilitator_guide(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "claude-sonnet-4"
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


async def generate_learner_guide(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "claude-sonnet-4"
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


async def generate_lesson_plan(
    course_data_json: str,
    organization_json: str,
    model_choice: str = "claude-sonnet-4"
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
