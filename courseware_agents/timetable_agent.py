"""
Timetable Generator Agent

Generates a lesson plan timetable from course context data
using the Claude Agent SDK with the barrier algorithm rules.
"""

import json
import os
from courseware_agents.base import run_agent_json

SYSTEM_PROMPT = """You are a WSQ timetable generator. Create lesson plans following strict scheduling rules.

DAILY SCHEDULE: 0930-1830hrs (9 hours)

FIXED SESSIONS (must appear every day):
- Day 1 Start: 0930-0945 (15min) - "Digital Attendance and Introduction" (N/A)
- Other Days: 0930-0940 (10min) - "Digital Attendance (AM)" (N/A)
- Morning Break: 1050-1100 (10min)
- Lunch: 1200-1245 (45min)
- PM Attendance: 1330-1340 (10min) - "Digital Attendance (PM)" (N/A)
- Afternoon Break: 1500-1510 (10min)
- End of Day: 1810-1830 (20min) - "Recap All Contents and Close"
- Last Day End: 1810-1830 (20min) - "Course Feedback and TRAQOM Survey"

BARRIER ALGORITHM RULES:
1. Topic duration = instructional_hours * 60 / num_topics minutes (equal allocation)
2. Topics CAN split across lunch/day-end barriers
3. When split: label "T2: Name" then "T2: Name (Cont'd)"
4. Minimum session: 15 minutes. If < 15 mins before barrier, use Break instead
5. Breaks fill all gaps so each day is exactly 0930-1830
6. LAST DAY must include assessment sessions before the closing

FINAL DAY ASSESSMENTS:
- Digital Attendance (Assessment) - 10min
- Assessment sessions based on Assessment_Methods_Details durations
- Place assessments in the afternoon of the last day

SESSION FORMAT:
- Topic: instruction_title="Topic X: [Title] (K#, A#)", bullet_points=[list of points]
- Activity: instruction_title="Activity: [Description]", bullet_points=[]
- Break/Lunch/Admin: instruction_title="[Name]", bullet_points=[], Instructional_Methods="N/A"

OUTPUT JSON:
{
    "lesson_plan": [
        {
            "Day": "Day 1",
            "Sessions": [
                {
                    "Time": "0930hrs - 0945hrs (15 mins)",
                    "instruction_title": "Digital Attendance and Introduction",
                    "bullet_points": [],
                    "Instructional_Methods": "N/A",
                    "Resources": "TV, Wi-Fi"
                }
            ]
        }
    ]
}

CRITICAL: Return ONLY valid JSON. No additional text or explanation.
"""


async def generate_timetable(
    context_path: str,
    output_path: str = None,
    custom_prompt: str = None,
) -> dict:
    """
    Generate a lesson plan timetable from course context.

    Args:
        context_path: Path to the context JSON file with course data.
        output_path: Path to save the updated context with timetable.
        custom_prompt: Optional custom prompt template to override default.

    Returns:
        Dict with 'lesson_plan' key containing the timetable.
    """
    if output_path is None:
        output_path = context_path  # Update in place

    # Read context
    with open(context_path, 'r', encoding='utf-8') as f:
        context = json.load(f)

    # Calculate number of days
    duration_str = context.get("Total_Course_Duration_Hours", "")
    if not duration_str:
        duration_str = context.get("Total_Training_Hours", "") or "16 hrs"
    hours = int(''.join(filter(str.isdigit, str(duration_str))) or "16")
    num_of_days = max(1, hours // 8)

    # Extract instructional methods
    from generate_ap_fg_lg_lp.utils.timetable_generator import extract_unique_instructional_methods
    list_of_im = extract_unique_instructional_methods(context)

    prompt = f"""Generate a lesson plan timetable for {num_of_days} day(s).

Available instructional methods: {list_of_im}

--- COURSE CONTEXT ---
{json.dumps(context, indent=2)}
--- END ---

Create the complete timetable following ALL the barrier algorithm rules.
Include ALL topics and bullet points from the course.
Resources for topics: "Slide page #", "TV", "Whiteboard", "Wi-Fi"

Return ONLY the JSON with the 'lesson_plan' key."""

    timetable = await run_agent_json(
        prompt=prompt,
        system_prompt=custom_prompt or SYSTEM_PROMPT,
        tools=["Read", "Glob"],
        max_turns=10,
    )

    # Merge timetable into context and save
    if 'lesson_plan' in timetable:
        context['lesson_plan'] = timetable['lesson_plan']
    else:
        context['lesson_plan'] = timetable

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=2, ensure_ascii=False)

    return timetable
