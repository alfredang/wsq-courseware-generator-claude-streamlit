"""
Slides Generation Module

Generates presentation slides from extracted course info using NotebookLM.
No file upload needed — uses course context from Extract Course Info page.

Flow:
1. User extracts course info on the Extract Course Info page
2. App formats the structured context as source text
3. App calls NotebookLM directly:
   - create notebook
   - add course content as source text
   - research internet for key topics (optional)
   - import research sources into notebook
   - generate slide deck with all sources
4. User gets slides in NotebookLM Studio

Dependencies:
    - streamlit
    - notebooklm-py[browser] (pip install notebooklm-py[browser])
"""

import streamlit as st
import asyncio
import logging
import re
import urllib.parse
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# =============================================================================
# Format course info as text for NotebookLM
# =============================================================================

def _format_course_info_as_text(context: dict) -> str:
    """
    Convert extracted course info dict to comprehensive structured text for NotebookLM.
    Follows the professional WSQ slide template standard with detailed content.

    Args:
        context: Course context dict from Extract Course Info page.

    Returns:
        Formatted text document suitable as a NotebookLM source.
    """
    lines = []

    course_title = context.get('Course_Title', 'Course')
    tgs_ref = context.get('TGS_Ref_No', '')
    tsc_title = context.get('TSC_Title', '')
    tsc_code = context.get('TSC_Code', '')
    duration = context.get('Total_Course_Duration_Hours', '')
    training_hours = context.get('Total_Training_Hours', '')

    # ── SLIDE 1: COVER ──
    lines.append(f"# {course_title}")
    lines.append("")
    if tgs_ref:
        lines.append(f"Course Code: {tgs_ref}")
    if tsc_code:
        lines.append(f"TSC Code: {tsc_code}")
    lines.append("")

    # ── SLIDE 2: DIGITAL ATTENDANCE ──
    lines.append("## Digital Attendance")
    lines.append("- It is mandatory for you to take both AM, PM and Assessment digital attendance for WSQ funded courses.")
    lines.append("- The trainer or administrator will show you the digital attendance QR code generated from SSG portal.")
    lines.append("- Please scan the QR code from your mobile phone camera and submit your attendance.")
    lines.append("")

    # ── SLIDE 3: LET'S KNOW EACH OTHER ──
    lines.append("## Let's Know Each Other")
    lines.append("- Name")
    lines.append("- Current role / company")
    lines.append("- Experience in the field")
    lines.append("- What do you hope to learn from this course?")
    lines.append("")

    # ── SLIDE 4: ABOUT THE TRAINER ──
    lines.append("## About the Trainer")
    lines.append("(Trainer introduction slide)")
    lines.append("")

    # ── SLIDE 5: GROUND RULES ──
    lines.append("## Ground Rules")
    lines.append("- Set your mobile phone to silent mode")
    lines.append("- Participate actively in the class. No question is stupid.")
    lines.append("- Mutual respect. Agree to disagree.")
    lines.append("- One conversation at one time.")
    lines.append("- Be punctual. Back from breaks on time.")
    lines.append("- Exit the class silently if you need to step out for phone call, toilet break etc.")
    lines.append("- 75% attendance is required for WSQ funding eligibility.")
    lines.append("")

    # ── SECTION 2: SKILLS FRAMEWORK ──
    lines.append("## Skills Framework")
    if tsc_title:
        lines.append(f"**TSC Title:** {tsc_title}")
    if tsc_code:
        lines.append(f"**TSC Code:** {tsc_code}")
    lines.append("")

    # TSC Description
    description = context.get('TSC_Description') or context.get('Proficiency_Description')
    if description:
        lines.append("### TSC Description")
        lines.append(description)
        lines.append("")

    # Collect ALL K&A statements across all LUs for the Skills Framework section
    all_k_statements = []
    all_a_statements = []
    for lu in context.get('Learning_Units', []):
        for k in lu.get('K_numbering_description', []):
            k_entry = f"**{k.get('K_number', '')}:** {k.get('Description', '')}"
            if k_entry not in all_k_statements:
                all_k_statements.append(k_entry)
        for a in lu.get('A_numbering_description', []):
            a_entry = f"**{a.get('A_number', '')}:** {a.get('Description', '')}"
            if a_entry not in all_a_statements:
                all_a_statements.append(a_entry)

    if all_k_statements:
        lines.append("### TSC Knowledge Statements")
        for k in all_k_statements:
            lines.append(f"- {k}")
        lines.append("")

    if all_a_statements:
        lines.append("### TSC Ability Statements")
        for a in all_a_statements:
            lines.append(f"- {a}")
        lines.append("")

    # ── SECTION 3: LEARNING OUTCOMES ──
    lines.append("## Learning Outcomes")
    for lu_idx, lu in enumerate(context.get('Learning_Units', []), 1):
        lo_num = lu.get('LO_Number', f'LO{lu_idx}')
        if lu.get('LO'):
            lines.append(f"- **{lo_num}:** {lu['LO']}")
    lines.append("")

    # ── SECTION 4: COURSE OUTLINE ──
    lines.append("## Course Outline")
    for lu_idx, lu in enumerate(context.get('Learning_Units', []), 1):
        lu_title = lu.get('LU_Title', 'Learning Unit')
        lu_num = lu.get('LU_Number', f'LU{lu_idx}')

        # Collect K&A numbers for this LU
        k_nums = [k.get('K_number', '') for k in lu.get('K_numbering_description', [])]
        a_nums = [a.get('A_number', '') for a in lu.get('A_numbering_description', [])]
        ka_refs = ', '.join(k_nums + a_nums)
        ka_str = f" ({ka_refs})" if ka_refs else ""

        lines.append(f"### {lu_num}: {lu_title}{ka_str}")
        for t_idx, topic in enumerate(lu.get('Topics', []), 1):
            topic_title = topic.get('Topic_Title', 'Topic')
            lines.append(f"- T{t_idx}: {topic_title}")
        lines.append("")

    # ── SECTION 5: ASSESSMENT INFORMATION ──
    assessment_details = context.get('Assessment_Methods_Details', [])
    if assessment_details:
        lines.append("## Final Assessment")
        for am in assessment_details:
            method = am.get('Assessment_Method', '')
            abbr = am.get('Method_Abbreviation', '')
            duration_am = am.get('Total_Delivery_Hours', '')
            label = f"{method} ({abbr})" if abbr else method
            lines.append(f"- {label} - {duration_am}")
        lines.append("- Assessment format: Open Book")
        lines.append("- Open book assessment ONLY includes Slides, Learner Guide or any approved materials.")
        lines.append("")

        lines.append("## Briefing for Assessment")
        lines.append("- Place phones and other materials under the table or on the floor")
        lines.append("- No photos or recording of assessment scripts")
        lines.append("- No discussion during assessment")
        lines.append("- Use black/blue pen for assessment (hard copies)")
        lines.append("- No usage of liquid paper or correction tape")
        lines.append("- Assessment scripts will be collected when time is up")
        lines.append("")

    # ── CRITERIA FOR FUNDING ──
    lines.append("## Criteria for Funding")
    lines.append("- Minimum attendance rate of 75% based on SSG Digital Attendance record.")
    lines.append("- Complete the assessment and be assessed as 'Competent'")
    lines.append("")

    # ── TRAQOM SURVEY ──
    lines.append("## Course Feedback and TRAQOM Survey")
    lines.append("- Please complete the TRAQOM survey at the end of the course.")
    lines.append("- Your feedback is important for continuous improvement.")
    lines.append("- The TRAQOM survey link will be provided by the trainer/administrator.")
    lines.append("")

    # ── SECTION 6: DETAILED TOPIC CONTENT (MAIN BODY) ──
    # Each LU becomes a major section with deep, expanded topic slides
    for lu_idx, lu in enumerate(context.get('Learning_Units', []), 1):
        lu_title = lu.get('LU_Title', 'Learning Unit')
        lu_num = lu.get('LU_Number', f'LU{lu_idx}')
        lo_num = lu.get('LO_Number', f'LO{lu_idx}')

        lines.append(f"## {lu_num}: {lu_title}")
        lines.append("")

        if lu.get('LO'):
            lines.append(f"**{lo_num} - Learning Outcome:** {lu['LO']}")
            lines.append("")

        for t_idx, topic in enumerate(lu.get('Topics', []), 1):
            topic_title = topic.get('Topic_Title', 'Topic')
            lines.append(f"### T{t_idx}: {topic_title}")
            lines.append("")

            # Include all bullet points as detailed content
            for bp in topic.get('Bullet_Points', []):
                lines.append(f"- {bp}")

            # Add instruction for deep content generation
            lines.append("")
            lines.append(f"NOTE: Create multiple detailed slides for this topic. "
                         f"Each major concept should have its own slide with "
                         f"explanations, examples, diagrams, and practical applications. "
                         f"Include comparison slides, summary slides, and real-world examples.")
            lines.append("")

        # K&A statements for this LU
        k_statements = lu.get('K_numbering_description', [])
        if k_statements:
            lines.append(f"### {lu_num} - Knowledge Statements")
            for k in k_statements:
                lines.append(f"- **{k.get('K_number', '')}:** {k.get('Description', '')}")
            lines.append("")

        a_statements = lu.get('A_numbering_description', [])
        if a_statements:
            lines.append(f"### {lu_num} - Ability Statements")
            for a in a_statements:
                lines.append(f"- **{a.get('A_number', '')}:** {a.get('Description', '')}")
            lines.append("")

        # Instructional methods
        methods = lu.get('Instructional_Methods', [])
        if methods:
            lines.append(f"**Instructional Methods:** {', '.join(methods)}")
            lines.append("")

    # ── CLOSING SLIDES ──
    lines.append("## Course Summary & Q&A")
    lines.append("Recap of all learning outcomes and key concepts covered.")
    for lu_idx, lu in enumerate(context.get('Learning_Units', []), 1):
        lo_num = lu.get('LO_Number', f'LO{lu_idx}')
        lu_title = lu.get('LU_Title', '')
        if lu.get('LO'):
            lines.append(f"- **{lo_num} ({lu_title}):** {lu['LO']}")
    lines.append("")
    lines.append("## Questions & Answers")
    lines.append("- Any questions?")
    lines.append("- Open discussion")
    lines.append("")

    lines.append("## Thank You")
    lines.append("Thank you for attending this course!")
    lines.append("We wish you all the best in applying what you have learned.")
    lines.append("")

    return "\n".join(lines)


def _format_lu_source_text(context: dict, lu_index: int, num_lus: int) -> str:
    """
    Format source text for a single Learning Unit's slide deck.

    Args:
        context: Full course context dict.
        lu_index: 0-based index of the LU to format.
        num_lus: Total number of LUs.

    Returns:
        Formatted text for one LU's NotebookLM source.
    """
    lines = []
    lus = context.get('Learning_Units', [])
    lu = lus[lu_index]

    course_title = context.get('Course_Title', 'Course')
    tgs_ref = context.get('TGS_Ref_No', '')
    tsc_title = context.get('TSC_Title', '')
    tsc_code = context.get('TSC_Code', '')
    lu_title = lu.get('LU_Title', 'Learning Unit')
    lu_num = lu.get('LU_Number', f'LU{lu_index + 1}')
    lo_num = lu.get('LO_Number', f'LO{lu_index + 1}')

    is_first = lu_index == 0
    is_last = lu_index == num_lus - 1

    # ── INTRO STANDARD PAGES (first LU only) ──
    if is_first:
        lines.append(f"# {course_title}")
        lines.append("")
        if tgs_ref:
            lines.append(f"Course Code: {tgs_ref}")
        if tsc_code:
            lines.append(f"TSC Code: {tsc_code}")
        lines.append("")

        lines.append("## Digital Attendance")
        lines.append("- It is mandatory for you to take both AM, PM and Assessment digital attendance for WSQ funded courses.")
        lines.append("- The trainer or administrator will show you the digital attendance QR code generated from SSG portal.")
        lines.append("- Please scan the QR code from your mobile phone camera and submit your attendance.")
        lines.append("")

        lines.append("## Let's Know Each Other")
        lines.append("- Name")
        lines.append("- Current role / company")
        lines.append("- Experience in the field")
        lines.append("- What do you hope to learn from this course?")
        lines.append("")

        lines.append("## About the Trainer")
        lines.append("(Trainer introduction slide)")
        lines.append("")

        lines.append("## Ground Rules")
        lines.append("- Set your mobile phone to silent mode")
        lines.append("- Participate actively in the class. No question is stupid.")
        lines.append("- Mutual respect. Agree to disagree.")
        lines.append("- One conversation at one time.")
        lines.append("- Be punctual. Back from breaks on time.")
        lines.append("- Exit the class silently if you need to step out for phone call, toilet break etc.")
        lines.append("- 75% attendance is required for WSQ funding eligibility.")
        lines.append("")

        # Skills Framework
        lines.append("## Skills Framework")
        if tsc_title:
            lines.append(f"**TSC Title:** {tsc_title}")
        if tsc_code:
            lines.append(f"**TSC Code:** {tsc_code}")
        lines.append("")

        description = context.get('TSC_Description') or context.get('Proficiency_Description')
        if description:
            lines.append("### TSC Description")
            lines.append(description)
            lines.append("")

        # All K&A statements
        all_k = []
        all_a = []
        for u in lus:
            for k in u.get('K_numbering_description', []):
                entry = f"**{k.get('K_number', '')}:** {k.get('Description', '')}"
                if entry not in all_k:
                    all_k.append(entry)
            for a in u.get('A_numbering_description', []):
                entry = f"**{a.get('A_number', '')}:** {a.get('Description', '')}"
                if entry not in all_a:
                    all_a.append(entry)
        if all_k:
            lines.append("### TSC Knowledge Statements")
            for k in all_k:
                lines.append(f"- {k}")
            lines.append("")
        if all_a:
            lines.append("### TSC Ability Statements")
            for a in all_a:
                lines.append(f"- {a}")
            lines.append("")

        # Learning Outcomes
        lines.append("## Learning Outcomes")
        for i, u in enumerate(lus, 1):
            lo = u.get('LO_Number', f'LO{i}')
            if u.get('LO'):
                lines.append(f"- **{lo}:** {u['LO']}")
        lines.append("")

        # Course Outline
        lines.append("## Course Outline")
        for i, u in enumerate(lus, 1):
            un = u.get('LU_Number', f'LU{i}')
            ut = u.get('LU_Title', 'Learning Unit')
            lines.append(f"### {un}: {ut}")
            for j, t in enumerate(u.get('Topics', []), 1):
                lines.append(f"- T{j}: {t.get('Topic_Title', 'Topic')}")
            lines.append("")

    # ── LU CONTENT (always included) ──
    lines.append(f"## {lu_num}: {lu_title}")
    lines.append("")
    if lu.get('LO'):
        lines.append(f"**{lo_num} - Learning Outcome:** {lu['LO']}")
        lines.append("")

    for t_idx, topic in enumerate(lu.get('Topics', []), 1):
        topic_title = topic.get('Topic_Title', 'Topic')
        lines.append(f"### T{t_idx}: {topic_title}")
        lines.append("")
        for bp in topic.get('Bullet_Points', []):
            lines.append(f"- {bp}")
        lines.append("")
        lines.append(
            f"NOTE: Create multiple detailed slides for this topic. "
            f"Each major concept should have its own slide with "
            f"explanations, examples, diagrams, and practical applications."
        )
        lines.append("")

    # K&A for this LU
    k_statements = lu.get('K_numbering_description', [])
    if k_statements:
        lines.append(f"### {lu_num} - Knowledge Statements")
        for k in k_statements:
            lines.append(f"- **{k.get('K_number', '')}:** {k.get('Description', '')}")
        lines.append("")

    a_statements = lu.get('A_numbering_description', [])
    if a_statements:
        lines.append(f"### {lu_num} - Ability Statements")
        for a in a_statements:
            lines.append(f"- **{a.get('A_number', '')}:** {a.get('Description', '')}")
        lines.append("")

    methods = lu.get('Instructional_Methods', [])
    if methods:
        lines.append(f"**Instructional Methods:** {', '.join(methods)}")
        lines.append("")

    # ── CLOSING PAGES (last LU only) ──
    if is_last:
        assessment_details = context.get('Assessment_Methods_Details', [])
        if assessment_details:
            lines.append("## Final Assessment")
            for am in assessment_details:
                method = am.get('Assessment_Method', '')
                abbr = am.get('Method_Abbreviation', '')
                dur = am.get('Total_Delivery_Hours', '')
                label = f"{method} ({abbr})" if abbr else method
                lines.append(f"- {label} - {dur}")
            lines.append("- Assessment format: Open Book")
            lines.append("- Open book assessment ONLY includes Slides, Learner Guide or any approved materials.")
            lines.append("")

            lines.append("## Briefing for Assessment")
            lines.append("- Place phones and other materials under the table or on the floor")
            lines.append("- No photos or recording of assessment scripts")
            lines.append("- No discussion during assessment")
            lines.append("- Use black/blue pen for assessment (hard copies)")
            lines.append("- No usage of liquid paper or correction tape")
            lines.append("- Assessment scripts will be collected when time is up")
            lines.append("")

        lines.append("## Criteria for Funding")
        lines.append("- Minimum attendance rate of 75% based on SSG Digital Attendance record.")
        lines.append("- Complete the assessment and be assessed as 'Competent'")
        lines.append("")

        lines.append("## Course Feedback and TRAQOM Survey")
        lines.append("- Please complete the TRAQOM survey at the end of the course.")
        lines.append("- Your feedback is important for continuous improvement.")
        lines.append("- The TRAQOM survey link will be provided by the trainer/administrator.")
        lines.append("")

        lines.append("## Course Summary & Q&A")
        lines.append("Recap of all learning outcomes and key concepts covered.")
        for i, u in enumerate(lus, 1):
            lo = u.get('LO_Number', f'LO{i}')
            ut = u.get('LU_Title', '')
            if u.get('LO'):
                lines.append(f"- **{lo} ({ut}):** {u['LO']}")
        lines.append("")
        lines.append("## Questions & Answers")
        lines.append("- Any questions?")
        lines.append("- Open discussion")
        lines.append("")

        lines.append("## Thank You")
        lines.append("Thank you for attending this course!")
        lines.append("We wish you all the best in applying what you have learned.")
        lines.append("")

    return "\n".join(lines)


def _format_chunk_source_text(context: dict, lu_index: int, num_lus: int,
                               topic_indices: list, chunk_label: str,
                               is_first_chunk_of_course: bool,
                               is_last_chunk_of_course: bool) -> str:
    """
    Format source text for a CHUNK of topics within a Learning Unit.

    This is used when an LU has many topics and we split them across
    multiple NotebookLM decks (~4-5 topics per deck for ~20 slides each).

    Args:
        context: Full course context dict.
        lu_index: 0-based index of the LU.
        num_lus: Total number of LUs.
        topic_indices: List of 0-based topic indices within this LU to include.
        chunk_label: Label like "Deck 1A", "Deck 1B" etc.
        is_first_chunk_of_course: Whether this is the very first chunk (include intro pages).
        is_last_chunk_of_course: Whether this is the very last chunk (include closing pages).

    Returns:
        Formatted text for this chunk's NotebookLM source.
    """
    lines = []
    lus = context.get('Learning_Units', [])
    lu = lus[lu_index]

    course_title = context.get('Course_Title', 'Course')
    tgs_ref = context.get('TGS_Ref_No', '')
    tsc_title = context.get('TSC_Title', '')
    tsc_code = context.get('TSC_Code', '')
    lu_title = lu.get('LU_Title', 'Learning Unit')
    lu_num = lu.get('LU_Number', f'LU{lu_index + 1}')
    lo_num = lu.get('LO_Number', f'LO{lu_index + 1}')

    # ── INTRO STANDARD PAGES (first chunk of course only) ──
    if is_first_chunk_of_course:
        lines.append(f"# {course_title}")
        lines.append("")
        if tgs_ref:
            lines.append(f"Course Code: {tgs_ref}")
        if tsc_code:
            lines.append(f"TSC Code: {tsc_code}")
        lines.append("")

        lines.append("## Digital Attendance")
        lines.append("- It is mandatory for you to take both AM, PM and Assessment digital attendance for WSQ funded courses.")
        lines.append("- The trainer or administrator will show you the digital attendance QR code generated from SSG portal.")
        lines.append("- Please scan the QR code from your mobile phone camera and submit your attendance.")
        lines.append("")

        lines.append("## Let's Know Each Other")
        lines.append("- Name")
        lines.append("- Current role / company")
        lines.append("- Experience in the field")
        lines.append("- What do you hope to learn from this course?")
        lines.append("")

        lines.append("## About the Trainer")
        lines.append("(Trainer introduction slide)")
        lines.append("")

        lines.append("## Ground Rules")
        lines.append("- Set your mobile phone to silent mode")
        lines.append("- Participate actively in the class. No question is stupid.")
        lines.append("- Mutual respect. Agree to disagree.")
        lines.append("- One conversation at one time.")
        lines.append("- Be punctual. Back from breaks on time.")
        lines.append("- Exit the class silently if you need to step out for phone call, toilet break etc.")
        lines.append("- 75% attendance is required for WSQ funding eligibility.")
        lines.append("")

        lines.append("## Skills Framework")
        if tsc_title:
            lines.append(f"**TSC Title:** {tsc_title}")
        if tsc_code:
            lines.append(f"**TSC Code:** {tsc_code}")
        lines.append("")

        description = context.get('TSC_Description') or context.get('Proficiency_Description')
        if description:
            lines.append("### TSC Description")
            lines.append(description)
            lines.append("")

        all_k = []
        all_a = []
        for u in lus:
            for k in u.get('K_numbering_description', []):
                entry = f"**{k.get('K_number', '')}:** {k.get('Description', '')}"
                if entry not in all_k:
                    all_k.append(entry)
            for a in u.get('A_numbering_description', []):
                entry = f"**{a.get('A_number', '')}:** {a.get('Description', '')}"
                if entry not in all_a:
                    all_a.append(entry)
        if all_k:
            lines.append("### TSC Knowledge Statements")
            for k in all_k:
                lines.append(f"- {k}")
            lines.append("")
        if all_a:
            lines.append("### TSC Ability Statements")
            for a in all_a:
                lines.append(f"- {a}")
            lines.append("")

        lines.append("## Learning Outcomes")
        for i, u in enumerate(lus, 1):
            lo = u.get('LO_Number', f'LO{i}')
            if u.get('LO'):
                lines.append(f"- **{lo}:** {u['LO']}")
        lines.append("")

        lines.append("## Course Outline")
        for i, u in enumerate(lus, 1):
            un = u.get('LU_Number', f'LU{i}')
            ut = u.get('LU_Title', 'Learning Unit')
            lines.append(f"### {un}: {ut}")
            for j, t in enumerate(u.get('Topics', []), 1):
                lines.append(f"- T{j}: {t.get('Topic_Title', 'Topic')}")
            lines.append("")

    # ── LU + TOPIC CHUNK CONTENT ──
    lines.append(f"## {lu_num}: {lu_title}")
    lines.append("")
    if lu.get('LO'):
        lines.append(f"**{lo_num} - Learning Outcome:** {lu['LO']}")
        lines.append("")

    topics = lu.get('Topics', [])
    for t_idx in topic_indices:
        if t_idx >= len(topics):
            continue
        topic = topics[t_idx]
        topic_title = topic.get('Topic_Title', 'Topic')
        lines.append(f"### T{t_idx + 1}: {topic_title}")
        lines.append("")
        for bp in topic.get('Bullet_Points', []):
            lines.append(f"- {bp}")
        lines.append("")
        lines.append(
            f"NOTE: Create multiple detailed slides for this topic. "
            f"Each major concept should have its own slide with "
            f"explanations, examples, diagrams, and practical applications."
        )
        lines.append("")

    # K&A for this LU
    k_statements = lu.get('K_numbering_description', [])
    if k_statements:
        lines.append(f"### {lu_num} - Knowledge Statements")
        for k in k_statements:
            lines.append(f"- **{k.get('K_number', '')}:** {k.get('Description', '')}")
        lines.append("")

    a_statements = lu.get('A_numbering_description', [])
    if a_statements:
        lines.append(f"### {lu_num} - Ability Statements")
        for a in a_statements:
            lines.append(f"- **{a.get('A_number', '')}:** {a.get('Description', '')}")
        lines.append("")

    # ── CLOSING PAGES (last chunk of course only) ──
    if is_last_chunk_of_course:
        assessment_details = context.get('Assessment_Methods_Details', [])
        if assessment_details:
            lines.append("## Final Assessment")
            for am in assessment_details:
                method = am.get('Assessment_Method', '')
                abbr = am.get('Method_Abbreviation', '')
                dur = am.get('Total_Delivery_Hours', '')
                label = f"{method} ({abbr})" if abbr else method
                lines.append(f"- {label} - {dur}")
            lines.append("- Assessment format: Open Book")
            lines.append("- Open book assessment ONLY includes Slides, Learner Guide or any approved materials.")
            lines.append("")

            lines.append("## Briefing for Assessment")
            lines.append("- Place phones and other materials under the table or on the floor")
            lines.append("- No photos or recording of assessment scripts")
            lines.append("- No discussion during assessment")
            lines.append("- Use black/blue pen for assessment (hard copies)")
            lines.append("- No usage of liquid paper or correction tape")
            lines.append("- Assessment scripts will be collected when time is up")
            lines.append("")

        lines.append("## Criteria for Funding")
        lines.append("- Minimum attendance rate of 75% based on SSG Digital Attendance record.")
        lines.append("- Complete the assessment and be assessed as 'Competent'")
        lines.append("")

        lines.append("## Course Feedback and TRAQOM Survey")
        lines.append("- Please complete the TRAQOM survey at the end of the course.")
        lines.append("- Your feedback is important for continuous improvement.")
        lines.append("- The TRAQOM survey link will be provided by the trainer/administrator.")
        lines.append("")

        lines.append("## Course Summary & Q&A")
        lines.append("Recap of all learning outcomes and key concepts covered.")
        for i, u in enumerate(lus, 1):
            lo = u.get('LO_Number', f'LO{i}')
            ut = u.get('LU_Title', '')
            if u.get('LO'):
                lines.append(f"- **{lo} ({ut}):** {u['LO']}")
        lines.append("")
        lines.append("## Questions & Answers")
        lines.append("- Any questions?")
        lines.append("- Open discussion")
        lines.append("")

        lines.append("## Thank You")
        lines.append("Thank you for attending this course!")
        lines.append("We wish you all the best in applying what you have learned.")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# NotebookLM helpers
# =============================================================================

def _check_notebooklm_available() -> bool:
    """Check if notebooklm-py library is installed."""
    try:
        from notebooklm import NotebookLMClient  # noqa: F401
        return True
    except ImportError:
        return False


def _extract_research_queries(content: str, course_title: str,
                               num_queries: int = 2) -> List[str]:
    """
    Extract research queries from document content by finding key topics.
    Pure text parsing — no LLM needed.
    """
    queries = []
    lines = content.split('\n')

    topic_candidates = []
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue

        if re.match(r'^#{2,3}\s+\w', stripped) and len(stripped) < 120:
            topic_candidates.append(re.sub(r'^#{2,3}\s+', '', stripped))
        elif re.match(r'^\d+\.?\d*\s+\w', stripped) and len(stripped) < 120:
            topic_candidates.append(re.sub(r'^\d+\.?\d*\s+', '', stripped))

    seen = set()
    unique_topics = []
    for t in topic_candidates:
        normalized = t.lower().strip()
        if normalized in seen or normalized in ('introduction', 'conclusion', 'summary',
                                                  'references', 'appendix', 'course description',
                                                  'assessment methods'):
            continue
        seen.add(normalized)
        unique_topics.append(t)

    for topic in unique_topics[:num_queries]:
        query = f"{topic} training best practices and latest industry standards"
        queries.append(query)

    if len(queries) < num_queries:
        queries.append(f"{course_title} course content latest developments and best practices")

    return queries[:num_queries]


def _build_platform_urls(topics: List[str]) -> List[Dict[str, str]]:
    """Build Wikipedia search URLs for the given topics."""
    urls = []
    for topic in topics[:5]:
        clean_topic = re.sub(r'[^\w\s\-]', '', topic).strip()
        if not clean_topic:
            continue
        wiki_query = urllib.parse.quote_plus(clean_topic)
        urls.append({
            "url": f"https://en.wikipedia.org/w/index.php?search={wiki_query}",
            "title": f"Wikipedia: {clean_topic[:60]}"
        })
    return urls


async def _add_platform_sources(client, notebook_id: str, topics: List[str],
                                 progress_callback=None) -> List[str]:
    """Add sources from Wikipedia to the notebook."""
    platform_urls = _build_platform_urls(topics)
    added_source_ids = []

    if not platform_urls:
        return added_source_ids

    if progress_callback:
        progress_callback(
            f"Adding {len(platform_urls)} Wikipedia sources...",
            30
        )

    for url_info in platform_urls:
        try:
            source = await client.sources.add_url(
                notebook_id, url_info["url"], wait=False
            )
            if source and hasattr(source, 'id'):
                added_source_ids.append(source.id)
                logger.info(f"Added platform source: {url_info['title']} -> {source.id}")
        except Exception as e:
            logger.info(f"Skipped platform source {url_info['url']}: {e}")

    return added_source_ids


async def _do_internet_research(client, notebook_id: str, queries: List[str],
                                 progress_callback=None) -> List[str]:
    """Perform web research using NotebookLM's Research API and import sources."""
    all_imported_source_ids = []
    total_queries = len(queries)

    for idx, query in enumerate(queries):
        query_num = idx + 1
        logger.info(f"Starting research query {query_num}/{total_queries}: {query}")

        if progress_callback:
            progress_callback(
                f"Step 5/8: Researching topic {query_num}/{total_queries}: {query[:60]}...",
                35 + (idx * 10)
            )

        try:
            task = await client.research.start(notebook_id, query, source="web", mode="fast")
            task_id = task.get("task_id") or task.get("report_id", "")

            poll_timeout = 60
            elapsed = 0
            poll_interval = 3
            research_result = None

            while elapsed < poll_timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                result = await client.research.poll(notebook_id)
                status = result.get("status", "")

                if status == "completed":
                    research_result = result
                    break
                elif status == "no_research":
                    break

            if not research_result:
                continue

            found_sources = research_result.get("sources", [])
            sources_to_import = [s for s in found_sources if s.get("url")][:5]

            if progress_callback:
                progress_callback(
                    f"Step 6/8: Importing {len(sources_to_import)} research sources...",
                    45 + (idx * 10)
                )

            if sources_to_import:
                try:
                    imported = await client.research.import_sources(
                        notebook_id, task_id, sources_to_import
                    )
                    for src in imported:
                        src_id = src.get("id") or src.get("source_id", "")
                        if src_id:
                            all_imported_source_ids.append(src_id)
                except Exception as e:
                    logger.warning(f"Failed to import sources for query '{query}': {e}")

        except Exception as e:
            logger.warning(f"Research failed for query '{query}': {e}")
            continue

    if all_imported_source_ids:
        if progress_callback:
            progress_callback(
                f"Waiting for {len(all_imported_source_ids)} research sources to process...",
                55
            )
        try:
            await client.sources.wait_for_sources(
                notebook_id, all_imported_source_ids, timeout=120.0
            )
        except Exception as e:
            logger.warning(f"Some research sources may not be ready: {e}")

    return all_imported_source_ids


async def _generate_slides_direct(content: str, course_title: str, config: Dict[str, Any],
                                   progress_callback=None) -> Dict[str, Any]:
    """
    Generate slides by calling NotebookLM directly.

    Args:
        content: Formatted course text for NotebookLM source
        course_title: Course title for the notebook name
        config: Slide configuration options
        progress_callback: Optional callback to update progress
    """
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        return {
            "success": False,
            "message": ("**notebooklm-py is not installed.**\n\n"
                        "Run: `pip install notebooklm-py[browser]`\n\n"
                        "Then authenticate: `python -m notebooklm login`")
        }

    enable_research = config.get('enable_research', True)
    num_queries = config.get('num_queries', 2)
    total_steps = 8 if enable_research else 5

    try:
        if progress_callback:
            progress_callback(f"Step 1/{total_steps}: Connecting to NotebookLM...", 5)

        client = await NotebookLMClient.from_storage()

        async with client:
            if progress_callback:
                progress_callback(f"Step 2/{total_steps}: Creating notebook...", 10)

            notebook_title = f"{course_title} - Slides"
            notebook = await client.notebooks.create(notebook_title)
            notebook_id = notebook.id

            if progress_callback:
                progress_callback(f"Step 3/{total_steps}: Uploading course content...", 15)

            source_title = f"{course_title} (Course Material)"
            source_text = content[:100000]
            source = await client.sources.add_text(notebook_id, source_title, source_text)
            source_id = source.id

            if progress_callback:
                progress_callback(f"Step 3/{total_steps}: Waiting for source processing...", 20)

            wait_time = min(15, max(8, len(source_text) // 10000))
            await asyncio.sleep(wait_time)

            try:
                sources_list = await client.sources.list(notebook_id)
                source_ready = any(s.id == source_id for s in sources_list)
                if not source_ready:
                    await asyncio.sleep(10)
            except Exception:
                await asyncio.sleep(5)

            all_source_ids = [source_id]
            research_sources_count = 0
            platform_sources_count = 0

            if enable_research:
                if progress_callback:
                    progress_callback(f"Step 4/{total_steps}: Extracting research topics...", 25)

                queries = _extract_research_queries(content, course_title, num_queries)

                if queries:
                    if progress_callback:
                        progress_callback(f"Step 4/{total_steps}: Adding Wikipedia sources...", 28)

                    topic_names = []
                    for q in queries:
                        core = re.sub(
                            r'\s+(training|best practices|latest|industry|standards|developments|course content).*$',
                            '', q, flags=re.IGNORECASE
                        ).strip()
                        if core:
                            topic_names.append(core)

                    platform_source_ids = await _add_platform_sources(
                        client, notebook_id, topic_names, progress_callback
                    )
                    all_source_ids.extend(platform_source_ids)
                    platform_sources_count = len(platform_source_ids)

                    research_source_ids = await _do_internet_research(
                        client, notebook_id, queries, progress_callback
                    )
                    all_source_ids.extend(research_source_ids)
                    research_sources_count = len(research_source_ids)

                    if platform_source_ids:
                        try:
                            await client.sources.wait_for_sources(
                                notebook_id, platform_source_ids, timeout=60.0
                            )
                        except Exception:
                            pass

            slide_step = 7 if enable_research else 4
            if progress_callback:
                progress_callback(f"Step {slide_step}/{total_steps}: Generating slide deck...", 65)

            slides_per_topic = config.get('slides_per_topic', 15)
            include_notes = config.get('include_notes', True)
            include_summaries = config.get('include_summaries', True)
            slide_style = config.get('slide_style', 'Professional')

            # Determine course duration for slide count target
            ctx = config.get('_context', {})
            course_hours = 0
            try:
                raw_hours = ctx.get('Total_Course_Duration_Hours', '') or ctx.get('Total_Training_Hours', '')
                course_hours = float(str(raw_hours).replace('hours', '').replace('hrs', '').replace('h', '').strip() or '0')
            except (ValueError, TypeError):
                course_hours = 8  # Default to 1-day

            # Slide count targets based on course duration
            num_topics = sum(
                len(lu.get('Topics', []))
                for lu in ctx.get('Learning_Units', [])
            ) or 10

            # Target ~5 slides per topic
            min_slides = max(num_topics * 5, 80)
            max_slides = min_slides + 40
            course_type = f"{course_hours}-hour"

            instructions = (
                f"Create a comprehensive {slide_style.lower()} slide deck for this WSQ training course. "
                f"This is for PROFESSIONAL CLIENT DELIVERY — quality and completeness are critical. "
                f"IMPORTANT: The cover/title slide MUST use exactly this title: \"{course_title}\". "
                "Do NOT rephrase, shorten, or change the course title in any way. "
                ""
                "CONTENT RULES: "
                "You MUST strictly follow the Course Proposal (CP) source material provided. "
                "All slide content must come directly from the source. "
                "Do NOT fabricate or invent information not in the source. "
                "However, you MUST expand each topic with detailed explanations, examples, "
                "diagrams, comparisons, and practical applications to create rich, educational content. "
                ""
                f"SLIDE COUNT: This is a {course_type} course ({course_hours} hours). "
                f"Generate between {min_slides} to {max_slides} slides total. "
                f"There are {num_topics} topics — each topic needs multiple detailed slides. "
                "15 slides is completely inadequate — generate comprehensive content. "
                ""
                "MANDATORY STANDARD PAGES (must appear in this exact order): "
                "1. COVER SLIDE — Course title, course code "
                "2. DIGITAL ATTENDANCE — WSQ digital attendance instructions "
                "3. LET'S KNOW EACH OTHER — Learner introduction slide "
                "4. ABOUT THE TRAINER — Trainer introduction slide "
                "5. GROUND RULES — Class rules and expectations "
                "6. LESSON PLAN — Day-by-day schedule overview "
                "7. SKILLS FRAMEWORK — TSC title, code, and description "
                "8. TSC KNOWLEDGE & ABILITY STATEMENTS — All K&A statements "
                "9. LEARNING OUTCOMES — All LOs listed clearly "
                "10. COURSE OUTLINE — All topics with K&A references "
                "11. ASSESSMENT INFO — Methods, format, briefing for assessment "
                "12. CRITERIA FOR FUNDING — Attendance and competency requirements "
                "13-onwards. TOPIC CONTENT — Deep, detailed slides for each LU and topic "
                "THEN: TRAQOM SURVEY — Course feedback instructions "
                "THEN: SUMMARY & Q&A — Recap all LOs and key takeaways "
                "FINAL: THANK YOU — Closing slide "
                ""
                "TOPIC CONTENT DEPTH: "
                "Each Learning Unit (LU1, LU2, LU3, etc.) must be a separate major section. "
                "Each section starts with a SECTION TITLE slide (e.g., 'LU1: Title'). "
                "Show the Learning Outcome on the section title or next slide. "
                "Each Topic (T1, T2, T3, etc.) must have MULTIPLE slides: "
                "- Title/overview slide for the topic "
                "- Detailed content slides with explanations "
                "- Comparison or diagram slides where relevant "
                "- Examples and real-world applications "
                "- Summary slide for each topic "
                "Include K&A statement references on relevant slides. "
                ""
                "VISUAL STYLE: "
                "Use a clean, light, modern design with white or light-colored backgrounds. "
                "Avoid dark themes. Use professional accent colors like blue (#4472C4). "
                "Use clear, readable fonts with good contrast. "
                "Include relevant images, diagrams, flowcharts, and icons throughout. "
                "Every few slides should have a visual element (diagram, chart, icon, image). "
            )
            if include_notes:
                instructions += "Include detailed speaker/facilitator notes for each slide. "
            if include_summaries:
                instructions += "Add a summary slide at the end of each LU section. "
            if enable_research and research_sources_count > 0:
                instructions += (
                    "Use research sources to supplement and enrich the CP content "
                    "with latest industry practices and real-world examples. "
                    "CP content takes priority — research adds depth. "
                )
            instructions += (
                f"REMEMBER: This is a {course_type} course. "
                f"Generate {min_slides}-{max_slides} slides. "
                "Quality AND quantity are both required for professional client delivery."
            )

            gen_result = None
            task_id = None
            for attempt in range(3):
                try:
                    if progress_callback and attempt > 0:
                        progress_callback(
                            f"Step {slide_step}/{total_steps}: Retrying (attempt {attempt + 1}/3)...",
                            70
                        )
                    gen_result = await client.artifacts.generate_slide_deck(
                        notebook_id,
                        source_ids=all_source_ids,
                        instructions=instructions,
                    )
                    task_id = gen_result.task_id if hasattr(gen_result, 'task_id') else str(gen_result)
                    break
                except Exception as e:
                    logger.warning(f"Slide generation attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(8)
                    else:
                        raise

            wait_step = 8 if enable_research else 5
            if progress_callback:
                progress_callback(
                    f"Step {wait_step}/{total_steps}: Waiting for slides (1-3 min)...",
                    80
                )

            generation_status = "triggered"
            if task_id:
                try:
                    await client.artifacts.wait_for_completion(
                        notebook_id, task_id, timeout=300.0
                    )
                    generation_status = "completed"
                except TimeoutError:
                    generation_status = "timeout"
                except Exception as e:
                    generation_status = f"wait_error: {e}"

            if progress_callback:
                progress_callback("Slides generated successfully!", 95)

            return {
                "success": True,
                "message": "Slide deck generated successfully!",
                "notebook_id": notebook_id,
                "notebook_title": notebook_title,
                "task_id": task_id,
                "generation_status": generation_status,
                "research_enabled": enable_research,
                "research_sources_count": research_sources_count,
                "platform_sources_count": platform_sources_count,
                "total_sources": len(all_source_ids),
            }

    except FileNotFoundError:
        return {
            "success": False,
            "message": ("**NotebookLM authentication not found.**\n\n"
                        "Run in your terminal:\n"
                        "```\nuv run notebooklm login\n```")
        }
    except Exception as e:
        error_msg = str(e)
        if "auth" in error_msg.lower() or "login" in error_msg.lower():
            return {
                "success": False,
                "message": (f"**NotebookLM authentication error:** {error_msg}\n\n"
                            "Please re-authenticate:\n"
                            "```\nuv run notebooklm login\n```")
            }
        return {
            "success": False,
            "message": f"**Error generating slides:** {error_msg}"
        }


async def _generate_slides_per_lu(context: dict, course_title: str,
                                   config: Dict[str, Any],
                                   progress_callback=None,
                                   skip_lu_indices: set = None) -> Dict[str, Any]:
    """
    Generate slides by splitting LU topics into chunks of ~4-5 topics each.

    Each chunk gets its own NotebookLM deck (~20 slides). Topics are split
    across multiple decks so every topic gets detailed coverage without
    repetition. E.g. LU1 with 13 topics → Deck 1A (T1-T5), 1B (T6-T10), 1C (T11-T13).

    Args:
        context: Full course context dict.
        course_title: Course title string.
        config: Slide generation config.
        progress_callback: Optional callback for UI progress updates.
        skip_lu_indices: Optional set of LU indices (0-based) to skip.
                         Used when resuming after a partial failure.

    Returns:
        Dict with success status and list of per-LU results.
    """
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        return {
            "success": False,
            "message": ("**notebooklm-py is not installed.**\n\n"
                        "Run: `pip install notebooklm-py[browser]`\n\n"
                        "Then authenticate: `python -m notebooklm login`")
        }

    lus = context.get('Learning_Units', [])
    num_lus = len(lus)
    if num_lus == 0:
        return {"success": False, "message": "No Learning Units found in course info."}

    enable_research = config.get('enable_research', True)
    num_queries = config.get('num_queries', 2)
    slide_style = config.get('slide_style', 'Professional')
    include_notes = config.get('include_notes', True)

    # ── Calculate target decks based on course duration ──
    # 1-day (~8hrs): ~80 slides = 4 decks × 20
    # 2-day (~16hrs): ~140 slides = 7 decks × 20
    # 3-day (~24hrs): ~200 slides = 10 decks × 20
    total_hours = context.get('Total_Course_Duration_Hours', '')
    try:
        hours = float(str(total_hours).replace('hrs', '').replace('hr', '').strip())
    except (ValueError, TypeError):
        hours = 8
    days = max(1, round(hours / 8))
    total_topics = sum(len(lu.get('Topics', [])) for lu in lus)
    SLIDES_PER_DECK = 20
    if days >= 3:
        target_decks = 11  # ~220 slides
    elif days >= 2:
        target_decks = 7
    else:
        target_decks = 4
    # Cap target to total topics (can't have more decks than topics)
    target_decks = min(target_decks, total_topics)

    # ── Distribute decks proportionally across LUs ──
    topic_counts = [len(lu.get('Topics', [])) for lu in lus if len(lu.get('Topics', [])) > 0]
    lu_indices_with_topics = [i for i in range(num_lus) if len(lus[i].get('Topics', [])) > 0]

    # Proportional allocation: each LU gets decks proportional to its topic count
    raw_alloc = [(tc / total_topics) * target_decks for tc in topic_counts]
    chunks_per_lu = [max(1, int(r)) for r in raw_alloc]
    # Distribute remaining decks to LUs with largest fractional parts
    remaining = target_decks - sum(chunks_per_lu)
    if remaining > 0:
        fracs = [(raw_alloc[i] - chunks_per_lu[i], i) for i in range(len(topic_counts))]
        fracs.sort(reverse=True)
        for _, idx in fracs[:remaining]:
            chunks_per_lu[idx] += 1
    # Ensure no LU has more chunks than topics
    for i, tc in enumerate(topic_counts):
        chunks_per_lu[i] = min(chunks_per_lu[i], tc)

    all_chunks = []
    chunk_idx = 0
    for alloc_idx, lu_idx in enumerate(lu_indices_with_topics):
        lu = lus[lu_idx]
        lu_num = lu.get('LU_Number', f'LU{lu_idx + 1}')
        lu_title = lu.get('LU_Title', 'Learning Unit')
        topics = lu.get('Topics', [])
        num_topics = len(topics)
        num_chunks = chunks_per_lu[alloc_idx]

        # Distribute topics evenly across this LU's chunks
        base = num_topics // num_chunks
        extra = num_topics % num_chunks
        topic_chunks = []
        start = 0
        for ci in range(num_chunks):
            size = base + (1 if ci < extra else 0)
            topic_chunks.append(list(range(start, start + size)))
            start += size

        # Label chunks: if only 1 chunk, just "LU1"; if multiple, "LU1-A", "LU1-B", etc.
        for ci, t_indices in enumerate(topic_chunks):
            if len(topic_chunks) == 1:
                label = lu_num
            else:
                letter = chr(65 + ci)  # A, B, C, ...
                label = f"{lu_num}-{letter}"
            all_chunks.append((chunk_idx, lu_idx, lu_num, lu_title, t_indices, label))
            chunk_idx += 1

    total_chunks = len(all_chunks)
    if total_chunks == 0:
        return {"success": False, "message": "No topics found in any Learning Unit."}

    lu_results = []

    try:
        if progress_callback:
            progress_callback("Connecting to NotebookLM...", 2)

        client = await NotebookLMClient.from_storage()

        if skip_lu_indices is None:
            skip_lu_indices = set()

        async with client:
            # ── Phase 1: Build chunk metadata (skip already completed) ──
            chunk_meta = []
            active_chunks = [c for c in all_chunks if c[0] not in skip_lu_indices]
            for chunk in all_chunks:
                c_idx, lu_idx, lu_num, lu_title, t_indices, label = chunk
                if c_idx in skip_lu_indices:
                    if progress_callback:
                        progress_callback(f"Skipping {label} (already completed)...", 5)
                    continue

                # First/last among ACTIVE (non-skipped) chunks for intro/closing pages
                is_first = (active_chunks[0][0] == c_idx) if active_chunks else False
                is_last = (active_chunks[-1][0] == c_idx) if active_chunks else False

                content = _format_chunk_source_text(
                    context, lu_idx, num_lus, t_indices, label,
                    is_first_chunk_of_course=is_first,
                    is_last_chunk_of_course=is_last
                )

                # Topic names for this chunk
                topics = lus[lu_idx].get('Topics', [])
                topic_names = [topics[ti].get('Topic_Title', f'T{ti+1}') for ti in t_indices if ti < len(topics)]
                topic_range = f"T{t_indices[0]+1}-T{t_indices[-1]+1}" if len(t_indices) > 1 else f"T{t_indices[0]+1}"

                chunk_meta.append({
                    'chunk_idx': c_idx,
                    'lu_idx': lu_idx,
                    'lu_num': lu_num,
                    'lu_title': lu_title,
                    'label': label,
                    'topic_indices': t_indices,
                    'topic_range': topic_range,
                    'topic_names': topic_names,
                    'num_topics': len(t_indices),
                    'content': content,
                    'is_first': is_first,
                    'is_last': is_last,
                })

            if not chunk_meta:
                return {"success": True, "message": "All decks already completed.", "lu_results": [], "num_lus": num_lus}

            if progress_callback:
                progress_callback(f"Creating {len(chunk_meta)} notebooks ({total_chunks} total decks)...", 5)

            # ── Create all notebooks concurrently ──
            async def _create_notebook(cm):
                nb_title = f"{course_title} - {cm['label']}: {cm['lu_title']} ({cm['topic_range']})"
                notebook = await client.notebooks.create(nb_title)
                return (cm, notebook.id, nb_title)

            nb_tasks = [_create_notebook(cm) for cm in chunk_meta]
            nb_results = await asyncio.gather(*nb_tasks, return_exceptions=True)

            active_chunks = []
            for res in nb_results:
                if isinstance(res, Exception):
                    logger.warning(f"Notebook creation failed: {res}")
                    continue
                active_chunks.append(res)

            if not active_chunks:
                return {"success": False, "message": "Failed to create any notebooks. Check NotebookLM quota."}

            if progress_callback:
                progress_callback(f"Adding source material to {len(active_chunks)} notebooks...", 15)

            # ── Add sources concurrently ──
            async def _add_source(cm, notebook_id):
                src_title = f"{course_title} - {cm['label']} (Course Material)"
                source_text = cm['content'][:100000]
                source = await client.sources.add_text(notebook_id, src_title, source_text)
                return source.id

            src_tasks = [_add_source(cm, nb_id) for (cm, nb_id, nb_title) in active_chunks]
            src_results = await asyncio.gather(*src_tasks, return_exceptions=True)

            await asyncio.sleep(3)

            if progress_callback:
                progress_callback(f"Generating {len(active_chunks)} slide decks...", 25)

            # ── Phase 2: Generate slide decks ──
            async def _generate_chunk_deck(cm, notebook_id, nb_title, source_id):
                all_source_ids = [source_id]
                research_count = 0

                if enable_research:
                    try:
                        queries = _extract_research_queries(cm['content'], course_title, num_queries)
                        if queries:
                            # Use NotebookLM's built-in research API
                            research_ids = await _do_internet_research(
                                client, notebook_id, queries
                            )
                            all_source_ids.extend(research_ids)
                            research_count = len(research_ids)

                            # Wait for sources to finish processing
                            if research_ids:
                                await asyncio.sleep(5)

                            # Clean up: remove ANY failed/error sources before generating slides
                            try:
                                sources_list = await client.sources.list(notebook_id)
                                for src in sources_list:
                                    src_id = getattr(src, 'id', None) or (src.get('id') if isinstance(src, dict) else None)
                                    status = getattr(src, 'status', None) or (src.get('status') if isinstance(src, dict) else None)
                                    status_str = str(status).lower() if status else ''
                                    if status_str in ('error', 'failed', 'invalid', 'unprocessable'):
                                        try:
                                            await client.sources.delete(notebook_id, src_id)
                                            if src_id in all_source_ids:
                                                all_source_ids.remove(src_id)
                                            logger.info(f"Removed failed source {src_id} (status: {status_str})")
                                        except Exception:
                                            pass
                            except Exception as e:
                                logger.warning(f"Source cleanup check failed: {e}")
                    except Exception as e:
                        logger.warning(f"{cm['label']} research failed: {e}")

                # Build instructions — ~20 slides per chunk, each topic gets 4-5 slides
                slides_target = SLIDES_PER_DECK + (5 if cm['is_first'] else 0)
                topic_list = ", ".join(cm['topic_names'])

                instructions = (
                    f"Create a {slide_style.lower()} presentation for this WSQ training course section. "
                    f"PROFESSIONAL CLIENT DELIVERY — quality is critical.\n\n"
                )

                if cm['is_first']:
                    instructions += (
                        f"TITLE: Use exactly \"{course_title}\" on the cover slide.\n\n"
                        "REQUIRED INTRO PAGES (in order):\n"
                        "1. Cover Slide (course title + code)\n"
                        "2. Digital Attendance (WSQ attendance instructions)\n"
                        "3. Let's Know Each Other (learner introductions)\n"
                        "4. About the Trainer — Simple slide with the title 'About the Trainer' and creative illustrations/icons. "
                        "Do NOT add photo placeholders, bio fields, or name fields. Just the heading with decorative design elements.\n"
                        "5. Ground Rules (class expectations)\n"
                        "6. Skills Framework (TSC title, code, description)\n"
                        "7. Knowledge & Ability Statements\n"
                        "8. Learning Outcomes\n"
                        "9. Course Outline\n\n"
                    )

                if cm['is_last']:
                    instructions += (
                        "REQUIRED CLOSING PAGES (at end):\n"
                        "- Assessment Info & Briefing\n"
                        "- Criteria for Funding (attendance + competency)\n"
                        "- TRAQOM Survey\n"
                        "- Summary & Q&A\n"
                        "- Thank You\n\n"
                    )

                instructions += (
                    f"SLIDE COUNT: ~{slides_target} slides for these topics ONLY:\n"
                    f"{topic_list}\n\n"
                    f"IMPORTANT: Cover ONLY the topics listed in the source material for this deck. "
                    f"Do NOT repeat content from other decks. Each topic gets 4-5 detailed slides.\n\n"
                    "CONTENT RULES:\n"
                    "- Strictly follow the source material. Do NOT fabricate information.\n"
                    "- Expand each topic with detailed explanations, examples, and practical applications.\n"
                    "- Each topic gets 4-5 slides: overview, detailed content, examples, key takeaways.\n"
                    "- Include K&A statement references on relevant slides.\n\n"
                    "MANDATORY DESIGN THEME — 'WSQ Professional Blue' (ALL slides MUST follow this exactly):\n"
                    "- BACKGROUND: Plain white (#FFFFFF) or very light grey (#F5F5F5) ONLY. "
                    "NO colored backgrounds, NO gradients, NO dark slides, NO blue backgrounds, NO images as backgrounds.\n"
                    "- PRIMARY COLOR: Dark navy blue (#1B3A5C) for all headings and section titles.\n"
                    "- SECONDARY COLOR: Teal (#2AA198) for accents, icons, and highlights.\n"
                    "- BODY TEXT: Dark grey (#333333), clean sans-serif font.\n"
                    "- CONSISTENCY: Every single slide must use this EXACT same color scheme and style. "
                    "All sections must look like they belong to the SAME presentation. "
                    "Do NOT change colors, fonts, or style between different topics or sections.\n"
                    "- CREATIVE ELEMENTS: Use relevant icons, simple illustrations, comparison tables, "
                    "process flowcharts, timeline diagrams, and infographic-style layouts.\n"
                    "- LAYOUT VARIETY: Side-by-side columns, numbered steps, "
                    "highlight boxes for key concepts, quote callouts for important points.\n"
                )

                if include_notes:
                    instructions += "\nInclude detailed speaker/facilitator notes for every slide."

                gen_result = None
                for attempt in range(3):
                    try:
                        gen_result = await client.artifacts.generate_slide_deck(
                            notebook_id,
                            source_ids=all_source_ids,
                            instructions=instructions,
                        )
                        break
                    except Exception as e:
                        logger.warning(f"{cm['label']} generation attempt {attempt + 1} failed: {e}")
                        if attempt < 2:
                            await asyncio.sleep(3)
                        else:
                            raise

                task_id = gen_result.task_id if hasattr(gen_result, 'task_id') else str(gen_result)

                generation_status = "triggered"
                if task_id:
                    try:
                        await client.artifacts.wait_for_completion(
                            notebook_id, task_id, timeout=300.0
                        )
                        generation_status = "completed"
                    except TimeoutError:
                        generation_status = "timeout"
                    except Exception as e:
                        generation_status = f"wait_error: {e}"

                return {
                    "lu_num": cm['label'],
                    "lu_title": f"{cm['lu_title']} ({cm['topic_range']})",
                    "notebook_id": notebook_id,
                    "notebook_title": nb_title,
                    "task_id": task_id,
                    "generation_status": generation_status,
                    "research_sources_count": research_count,
                    "total_sources": len(all_source_ids),
                    "chunk_idx": cm['chunk_idx'],
                }

            # Run all chunk generations concurrently
            gen_tasks = []
            for i, (cm, nb_id, nb_title) in enumerate(active_chunks):
                src_id = src_results[i] if not isinstance(src_results[i], Exception) else None
                if src_id is None:
                    logger.warning(f"Skipping {cm['label']} — source add failed")
                    continue
                gen_tasks.append(_generate_chunk_deck(cm, nb_id, nb_title, src_id))

            gen_results = await asyncio.gather(*gen_tasks, return_exceptions=True)

            for i, res in enumerate(gen_results):
                if isinstance(res, Exception):
                    logger.warning(f"Chunk generation failed: {res}")
                    continue
                lu_results.append(res)
                if progress_callback:
                    pct = int(((i + 1) / len(gen_results)) * 70) + 25
                    progress_callback(
                        f"{res['lu_num']} slides generated ({res['generation_status']})",
                        pct
                    )

        if progress_callback:
            progress_callback("All slide decks generated!", 95)

        generated_count = len(lu_results)
        skipped_count = len(skip_lu_indices)
        msg = f"Generated {generated_count} slide deck(s) across {num_lus} LUs."
        if skipped_count:
            msg += f" (Skipped {skipped_count} already completed.)"

        return {
            "success": True,
            "message": msg,
            "lu_results": lu_results,
            "num_lus": num_lus,
            "total_chunks": total_chunks,
            "is_resume": bool(skip_lu_indices),
        }

    except FileNotFoundError:
        return {
            "success": False,
            "message": ("**NotebookLM authentication not found.**\n\n"
                        "Run in your terminal:\n```\nuv run notebooklm login\n```")
        }
    except Exception as e:
        error_msg = str(e)
        completed = [r["lu_num"] for r in lu_results]
        if "auth" in error_msg.lower() or "login" in error_msg.lower():
            return {
                "success": False,
                "message": (f"**NotebookLM authentication error:** {error_msg}\n\n"
                            "Please re-authenticate:\n```\nuv run notebooklm login\n```"),
                "lu_results": lu_results,
            }
        return {
            "success": False,
            "message": (f"**Error generating slides:** {error_msg}\n\n"
                        f"Completed decks: {', '.join(completed) if completed else 'None'}"),
            "lu_results": lu_results,
        }


# =============================================================================
# NotebookLM logo removal from PPTX
# =============================================================================

def _remove_notebooklm_logo(pptx_bytes: bytes, progress_container=None) -> bytes:
    """
    Remove NotebookLM branding/logo from a PPTX file permanently.

    Simple, reliable approach:
    1. ZIP-level: Edit ALL slide images — paint over bottom-right logo area
    2. XML-level: Remove any shape elements containing NotebookLM text

    Args:
        pptx_bytes: Raw bytes of the uploaded PPTX file.
        progress_container: Optional Streamlit container for debug output.

    Returns:
        Cleaned PPTX file as bytes with NotebookLM branding removed.
    """
    import io
    import zipfile
    from PIL import Image
    from lxml import etree

    removed_count = 0
    details = []

    def _log(msg):
        """Log to both logger and optional Streamlit container."""
        logger.info(msg)
        if progress_container:
            try:
                progress_container.caption(msg)
            except Exception:
                pass

    _log("Starting NotebookLM logo removal...")

    # ═══════════════════════════════════════════════════════════════════
    # SINGLE PASS: Process the entire PPTX as a ZIP archive
    # Edit images (paint over logo) + clean XML (remove text shapes)
    # ═══════════════════════════════════════════════════════════════════
    input_zip = zipfile.ZipFile(io.BytesIO(pptx_bytes), 'r')
    output_buf = io.BytesIO()
    output_zip = zipfile.ZipFile(output_buf, 'w', zipfile.ZIP_DEFLATED)

    images_found = 0
    images_processed = 0
    images_failed = 0

    for item in input_zip.infolist():
        data = input_zip.read(item.filename)
        fname_lower = item.filename.lower()

        # ── Detect images ──
        is_media = 'ppt/media/' in fname_lower
        is_image_ext = fname_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'))
        is_image_magic = (
            len(data) > 4 and (
                data[:4] == b'\x89PNG' or
                data[:2] == b'\xff\xd8' or
                data[:6] in (b'GIF87a', b'GIF89a') or
                data[:2] == b'BM'
            )
        )

        if is_media or is_image_ext or is_image_magic:
            try:
                img = Image.open(io.BytesIO(data))
                w, h = img.size
                images_found += 1

                # Process slide-sized images (skip tiny icons/thumbnails)
                if w >= 400 and h >= 200:
                    new_data = _erase_logo_region(img)
                    if new_data:
                        # Verify the output is valid
                        verify = Image.open(io.BytesIO(new_data))
                        if verify.size == (w, h):
                            data = new_data
                            images_processed += 1
                            removed_count += 1
                        else:
                            _log(f"  WARNING: {item.filename} — output size mismatch {verify.size} != {(w, h)}")
                            images_failed += 1
                    else:
                        _log(f"  WARNING: {item.filename} — _erase_logo_region returned None")
                        images_failed += 1
            except Exception as e:
                details.append(f"Cannot open {item.filename}: {type(e).__name__}")
                _log(f"  Cannot open {item.filename}: {e}")

        # ── Clean XML: remove shapes with NotebookLM text ──
        elif fname_lower.endswith(('.xml', '.rels')):
            try:
                text_content = data.decode('utf-8', errors='replace')
                if 'notebooklm' in text_content.lower() or 'notebook lm' in text_content.lower():
                    _log(f"  Found NotebookLM text in {item.filename}")

                    # Try XML parsing first
                    try:
                        root = etree.fromstring(data)
                        modified = False

                        for text_elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
                            if text_elem.text and 'notebooklm' in text_elem.text.lower():
                                parent = text_elem
                                sp_elem = None
                                for _ in range(20):
                                    parent = parent.getparent()
                                    if parent is None:
                                        break
                                    tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
                                    if tag in ('sp', 'grpSp', 'pic', 'cxnSp'):
                                        sp_elem = parent
                                        break
                                if sp_elem is not None and sp_elem.getparent() is not None:
                                    sp_elem.getparent().remove(sp_elem)
                                    modified = True
                                    removed_count += 1
                                    _log(f"  Removed XML shape from {item.filename}")
                                    break

                        if modified:
                            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
                    except etree.XMLSyntaxError:
                        pass

                    # String replacement fallback
                    text_content = data.decode('utf-8', errors='replace')
                    if 'notebooklm' in text_content.lower():
                        text_content = text_content.replace('NotebookLM', '').replace('notebooklm', '')
                        text_content = text_content.replace('Notebook LM', '').replace('notebook lm', '')
                        data = text_content.encode('utf-8')
                        removed_count += 1
                        _log(f"  String-replaced in {item.filename}")
            except Exception:
                pass

        output_zip.writestr(item, data)

    input_zip.close()
    output_zip.close()
    output_buf.seek(0)

    summary = (
        f"Logo removal complete: {images_found} images found, "
        f"{images_processed} processed, {images_failed} failed"
    )
    _log(summary)
    logger.info(f"Details: {'; '.join(details[:20])}")

    return output_buf.read(), removed_count


def _diagnose_pptx(pptx_bytes: bytes) -> str:
    """Inspect a PPTX file and return diagnostic info about its contents."""
    import io
    import zipfile
    from PIL import Image

    lines = []
    try:
        z = zipfile.ZipFile(io.BytesIO(pptx_bytes), 'r')
        lines.append(f"Total files in PPTX: {len(z.namelist())}")

        images = []
        xmls_with_nlm = []

        for name in z.namelist():
            lower = name.lower()
            # Check images
            if any(lower.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.emf', '.wmf', '.svg')):
                data = z.read(name)
                try:
                    img = Image.open(io.BytesIO(data))
                    images.append(f"  {name}: {img.size[0]}x{img.size[1]} {img.mode} ({img.format})")
                except Exception:
                    images.append(f"  {name}: {len(data)} bytes (cannot open as image)")

            # Check XML for NotebookLM references
            elif lower.endswith('.xml'):
                try:
                    text = z.read(name).decode('utf-8', errors='replace')
                    if 'notebooklm' in text.lower():
                        # Find context around the match
                        idx = text.lower().find('notebooklm')
                        snippet = text[max(0, idx-100):idx+100]
                        xmls_with_nlm.append(f"  {name}: ...{snippet}...")
                except Exception:
                    pass

        lines.append(f"\nImages found: {len(images)}")
        lines.extend(images[:30])

        lines.append(f"\nXML files with 'NotebookLM': {len(xmls_with_nlm)}")
        lines.extend(xmls_with_nlm[:20])

        if not xmls_with_nlm and not images:
            lines.append("\nWARNING: No images and no NotebookLM text found!")

        z.close()
    except Exception as e:
        lines.append(f"Error: {e}")

    return "\n".join(lines)


def _erase_logo_region(img):
    """
    Erase the NotebookLM logo from a slide image.

    Simple left-clone approach with a VERY TIGHT region:
    - Region: 8% width × 3% height (just the logo, nothing else)
    - For each row, clone the pixel from just left of the region
    - No above-reference (avoids text streak artifacts)

    Returns modified image as bytes, or None on failure.
    """
    import io

    try:
        w, h = img.size
        original_format = img.format or 'PNG'

        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')

        # Logo region: 8% width × 3% height — covers NotebookLM branding only
        logo_region_w = max(int(w * 8 / 100), 70)
        logo_region_h = max(int(h * 0.03), 23)
        logo_left = w - logo_region_w
        logo_top = h - logo_region_h

        pixels = img.load()

        # Get the background color at the right edge (above the logo)
        # This tells us what the slide background is at the far right
        right_bg = pixels[min(w - 1, w - 3), max(0, logo_top - 3)]

        for y in range(logo_top, h):
            left_color = pixels[max(0, logo_left - 1), y]

            # Check if left color matches the right-edge background
            dist = (abs(left_color[0] - right_bg[0]) +
                    abs(left_color[1] - right_bg[1]) +
                    abs(left_color[2] - right_bg[2]))

            if dist < 50:
                # Uniform background — simple left-clone
                for x in range(logo_left, w):
                    pixels[x, y] = left_color
            else:
                # Bar on the left doesn't extend to right edge
                # Use left-clone but check each X: if the pixel ABOVE
                # matches the bar → continue bar, otherwise → use right_bg
                for x in range(logo_left, w):
                    above_c = pixels[x, max(0, logo_top - 3)]
                    dist_to_bar = (abs(above_c[0] - left_color[0]) +
                                   abs(above_c[1] - left_color[1]) +
                                   abs(above_c[2] - left_color[2]))
                    dist_to_bg = (abs(above_c[0] - right_bg[0]) +
                                  abs(above_c[1] - right_bg[1]) +
                                  abs(above_c[2] - right_bg[2]))

                    if dist_to_bar <= dist_to_bg:
                        pixels[x, y] = left_color  # bar continues here
                    else:
                        pixels[x, y] = right_bg  # bar ended, use background

        # ── Save ──
        out = io.BytesIO()
        if original_format.upper() == 'JPEG':
            save_img = img.convert('RGB') if img.mode == 'RGBA' else img
            save_img.save(out, format='JPEG', quality=95)
        else:
            img.save(out, format='PNG')
        out.seek(0)
        return out.read()

    except Exception as e:
        logger.error(f"_erase_logo_region failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def _combine_pptx_files(pptx_files: List[bytes], remove_logo: bool = True) -> tuple:
    """
    Combine multiple PPTX files into one and optionally remove NotebookLM logos.

    Uses the first file as the base presentation, then appends slides from
    subsequent files by copying slide XML and relationships.

    Args:
        pptx_files: List of PPTX file bytes to combine.
        remove_logo: Whether to remove NotebookLM branding.

    Returns:
        Tuple of (combined PPTX bytes, total slide count, logos removed count).
    """
    import io
    from pptx import Presentation
    from copy import deepcopy
    from lxml import etree

    if not pptx_files:
        raise ValueError("No PPTX files provided.")

    if len(pptx_files) == 1:
        if remove_logo:
            clean, count = _remove_notebooklm_logo(pptx_files[0])
            prs = Presentation(io.BytesIO(clean))
            return clean, len(prs.slides), count
        else:
            prs = Presentation(io.BytesIO(pptx_files[0]))
            output = io.BytesIO()
            prs.save(output)
            output.seek(0)
            return output.read(), len(prs.slides), 0

    # Load base presentation (first file)
    base_prs = Presentation(io.BytesIO(pptx_files[0]))

    # Append slides from remaining files
    for file_bytes in pptx_files[1:]:
        src_prs = Presentation(io.BytesIO(file_bytes))
        for slide in src_prs.slides:
            # Copy slide layout from source — use blank or first available in base
            slide_layout = base_prs.slide_layouts[6] if len(base_prs.slide_layouts) > 6 else base_prs.slide_layouts[0]
            new_slide = base_prs.slides.add_slide(slide_layout)

            # Clear default placeholders from new slide
            for ph in list(new_slide.placeholders):
                sp = ph._element
                sp.getparent().remove(sp)

            # Copy all shapes from source slide
            for shape in slide.shapes:
                el = deepcopy(shape._element)
                new_slide.shapes._spTree.append(el)

            # Copy slide background if present
            src_bg = slide._element.find(
                '{http://schemas.openxmlformats.org/presentationml/2006/main}bg'
            )
            if src_bg is not None:
                new_bg = deepcopy(src_bg)
                existing_bg = new_slide._element.find(
                    '{http://schemas.openxmlformats.org/presentationml/2006/main}bg'
                )
                if existing_bg is not None:
                    new_slide._element.replace(existing_bg, new_bg)
                else:
                    new_slide._element.insert(0, new_bg)

    total_slides = len(base_prs.slides)

    # Save combined, then remove logos
    output = io.BytesIO()
    base_prs.save(output)
    output.seek(0)
    combined_bytes = output.read()

    logos_removed = 0
    if remove_logo:
        combined_bytes, logos_removed = _remove_notebooklm_logo(combined_bytes)

    logger.info(f"Combined {len(pptx_files)} PPTX files: {total_slides} slides, {logos_removed} logos removed")
    return combined_bytes, total_slides, logos_removed


# =============================================================================
# Streamlit App
# =============================================================================

def app():
    """Streamlit page for Slides Generation."""
    st.title("Generate Slides")
    st.write("Generate presentation slides from course info using NotebookLM.")
    st.caption("Splits each LU into topic chunks (~20 slides per deck), then combine them all.")

    # Check dependencies
    nlm_available = _check_notebooklm_available()
    if not nlm_available:
        st.error(
            "**notebooklm-py library not installed.**\n\n"
            "Run: `pip install notebooklm-py[browser]`\n\n"
            "Then authenticate: `python -m notebooklm login`"
        )
        return

    # Prompt Templates (editable, collapsed)
    from utils.prompt_template_editor import render_prompt_templates
    render_prompt_templates("slides", "Prompt Templates (Slides)")

    # =================================================================
    # Section 1: Generate Slides per LU (requires extracted course info)
    # =================================================================
    extracted_info = st.session_state.get('extracted_course_info')
    if not extracted_info:
        st.warning("Please extract course info first on the **Extract Course Info** page to generate slides.")
    else:
        course_title = extracted_info.get('Course_Title', 'Course')
        lus = extracted_info.get('Learning_Units', [])
        num_lus = len(lus)
        num_topics = sum(len(lu.get('Topics', [])) for lu in lus)
        # Dynamic target decks based on course duration
        total_hours = extracted_info.get('Total_Course_Duration_Hours', '')
        try:
            _hours = float(str(total_hours).replace('hrs', '').replace('hr', '').strip())
        except (ValueError, TypeError):
            _hours = 8
        _days = max(1, round(_hours / 8))
        _slides_per_deck = 20
        if _days >= 3:
            _target = 11  # ~220 slides
        elif _days >= 2:
            _target = 7
        else:
            _target = 4
        _target = min(_target, num_topics)

        # Proportional deck allocation per LU
        _topic_counts = [len(lu.get('Topics', [])) for lu in lus if len(lu.get('Topics', [])) > 0]
        _lu_with_topics = [i for i in range(num_lus) if len(lus[i].get('Topics', [])) > 0]
        _raw = [max(1, (tc / num_topics) * _target) for tc in _topic_counts]
        _chunks_per = [max(1, int(r)) for r in _raw]
        _rem = _target - sum(_chunks_per)
        if _rem > 0:
            _fracs = [(_raw[i] - _chunks_per[i], i) for i in range(len(_topic_counts))]
            _fracs.sort(reverse=True)
            for _, _fi in _fracs[:_rem]:
                _chunks_per[_fi] += 1
        for _i, _tc in enumerate(_topic_counts):
            _chunks_per[_i] = min(_chunks_per[_i], _tc)

        total_decks = sum(_chunks_per)
        total_target = total_decks * _slides_per_deck
        st.caption(f"**{course_title}** | {num_lus} LUs | {num_topics} topics | **{total_decks} decks** | ~{total_target} slides target (~{_slides_per_deck}/deck)")

        from utils.agent_runner import submit_agent_job
        from utils.agent_status import render_page_job_status

        # ── Build deck list for selection ──
        deck_options = []
        _ci = 0
        for _ai, lu_idx in enumerate(_lu_with_topics):
            lu = lus[lu_idx]
            lu_num = lu.get('LU_Number', f'LU{lu_idx + 1}')
            lu_title = lu.get('LU_Title', 'Learning Unit')
            topics = lu.get('Topics', [])
            num_t = len(topics)
            n_chunks = _chunks_per[_ai]
            base = num_t // n_chunks
            extra = num_t % n_chunks
            start = 0
            topic_chunks = []
            for ci in range(n_chunks):
                size = base + (1 if ci < extra else 0)
                topic_chunks.append((start, start + size))
                start += size
            for ci_inner, (t_start, t_end) in enumerate(topic_chunks):
                if len(topic_chunks) == 1:
                    label = f"{lu_num}: {lu_title} (T{t_start+1}-T{t_end})"
                else:
                    letter = chr(65 + ci_inner)
                    label = f"{lu_num}-{letter}: {lu_title} (T{t_start+1}-T{t_end})"
                deck_options.append((_ci, label))
                _ci += 1

        # Deck selector — default all selected
        all_labels = [d[1] for d in deck_options]
        selected_labels = st.multiselect(
            "Select decks to generate",
            options=all_labels,
            default=all_labels,
            help="Uncheck decks you already have. Only selected decks will be generated."
        )
        # Map selected labels back to chunk indices to skip
        selected_indices = {d[0] for d in deck_options if d[1] in selected_labels}
        all_indices = {d[0] for d in deck_options}
        skip_indices = all_indices - selected_indices

        # Generate button
        if st.button("Generate Slides", type="primary"):
            _info = extracted_info
            _title = course_title
            _config = {
                'enable_research': True,
                'num_queries': 2,
                'include_notes': True,
                'slide_style': 'Professional',
            }
            _skip = skip_indices.copy() if skip_indices else None

            async def _generate_slides():
                return await _generate_slides_per_lu(_info, _title, _config, skip_lu_indices=_skip)

            # Clear previous results for fresh generation
            st.session_state.pop('slides_result', None)
            job = submit_agent_job(
                key="generate_slides",
                label="Generate Slides",
                async_fn=_generate_slides,
            )

            if job is None:
                st.warning("Slide generation is already running.")
            else:
                st.rerun()

        # Agent Status
        def _on_slides_complete(job):
            result = job.get("result")
            if result:
                st.session_state['slides_result'] = result

        job_status = render_page_job_status(
            "generate_slides",
            on_complete=_on_slides_complete,
            running_message=f"Generating {len(selected_indices)} slide decks via NotebookLM... (approximately {len(selected_indices) * 3}-{len(selected_indices) * 5} minutes)",
        )

        if job_status == "running":
            st.stop()

        # Display Results
        result = st.session_state.get('slides_result')
        if result:
            lu_results = result.get('lu_results', [])

            if result.get("success"):
                st.success(f"Generated {len(lu_results)} slide decks!")

                st.info(
                    "**Next steps:**\n"
                    "1. Open each LU notebook in NotebookLM (links below)\n"
                    "2. Download each slide deck as PDF\n"
                    "3. Upload all PDFs below → **Merge PDFs** → download one merged PDF\n"
                    "4. Convert the merged PDF to PPTX (e.g. using Canva) — just one conversion!\n"
                    "5. Upload the PPTX below → **Remove Logo** → download clean PPTX"
                )

                # Show link for each LU notebook
                for lr in lu_results:
                    nb_id = lr.get('notebook_id', '')
                    link = f"https://notebooklm.google.com/notebook/{nb_id}" if nb_id else ""
                    status = lr.get('generation_status', 'unknown')
                    status_icon = "+" if status == "completed" else "~"
                    st.markdown(
                        f"**{lr['lu_num']}: {lr['lu_title']}** — "
                        f"[Open in NotebookLM]({link}) ({status})"
                    )

                with st.expander("Generation Details"):
                    for lr in lu_results:
                        st.markdown(
                            f"- **{lr['lu_num']}:** {lr['notebook_title']} | "
                            f"Sources: {lr.get('total_sources', 1)} | "
                            f"Status: {lr.get('generation_status', 'N/A')}"
                        )
            else:
                st.error("Slide generation failed.")
                st.markdown(result.get("message", "Unknown error occurred."))
                # Show any partially completed LU results
                if lu_results:
                    st.warning(
                        f"Partially completed: {len(lu_results)} deck(s). "
                        f"Switch account if needed, then uncheck completed decks and click **Generate Slides** to continue."
                    )
                    for lr in lu_results:
                        nb_id = lr.get('notebook_id', '')
                        link = f"https://notebooklm.google.com/notebook/{nb_id}" if nb_id else ""
                        st.markdown(f"- **{lr['lu_num']}:** [Open in NotebookLM]({link})")

    # =================================================================
    # Section 2: Merge PDFs (always visible)
    # =================================================================
    st.divider()
    st.subheader("Step 1: Merge LU PDFs")
    st.caption(
        "Upload all LU slide deck PDFs downloaded from NotebookLM. "
        "They will be merged into one PDF — then convert that single PDF to PPTX via Canva."
    )

    uploaded_pdfs = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_merger",
    )

    if uploaded_pdfs:
        # Sort files by LU number + chunk letter (LU1-A, LU1-B, LU1-C, LU2-A, etc.)
        def _extract_lu_order(f):
            name = f.name.upper()
            # Match "LU1-A", "LU1-B", "LU2", "LU3-C" etc.
            m = re.search(r'LU\s*(\d+)\s*[-_]?\s*([A-Z])?', name)
            if m:
                lu_num = int(m.group(1))
                chunk_letter = m.group(2) or ''  # A, B, C or empty
                return (lu_num, chunk_letter)
            # Fallback: try to find any number
            m = re.search(r'(\d+)', name)
            if m:
                return (int(m.group(1)), '')
            return (999, '')  # Put unnumbered files at the end

        sorted_pdfs = sorted(uploaded_pdfs, key=_extract_lu_order)
        st.caption(f"{len(sorted_pdfs)} PDF(s) — merge order: {', '.join(f.name for f in sorted_pdfs)}")

        if st.button("Merge PDFs", type="primary"):
            with st.spinner(f"Merging {len(sorted_pdfs)} PDF files..."):
                try:
                    from pypdf import PdfReader, PdfWriter
                    import io

                    writer = PdfWriter()
                    total_pages = 0
                    for pdf_file in sorted_pdfs:
                        pdf_bytes = pdf_file.read()
                        reader = PdfReader(io.BytesIO(pdf_bytes))
                        for page in reader.pages:
                            writer.add_page(page)
                        total_pages += len(reader.pages)

                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)
                    merged_bytes = output.read()

                    st.success(f"Merged into **{total_pages} pages** from {len(uploaded_pdfs)} PDFs")

                    course_name = st.session_state.get('extracted_course_info', {}).get('Course_Title', 'Slides')
                    safe_name = re.sub(r'[^\w\s\-]', '', course_name).strip().replace(' ', '_')[:50]
                    pdf_filename = f"{safe_name}_merged.pdf"

                    st.download_button(
                        label=f"Download Merged PDF ({total_pages} pages)",
                        data=merged_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        type="primary",
                    )

                    st.info("**Next:** Convert this merged PDF to PPTX using Canva, then upload the PPTX below to remove the NotebookLM logo.")
                except Exception as e:
                    st.error(f"Error merging PDFs: {e}")
                    logger.exception("PDF merge error")

    # =================================================================
    # Section 3: Remove Logo from PPTX (always visible)
    # =================================================================
    st.divider()
    st.subheader("Step 2: Remove NotebookLM Logo from PPTX")
    st.caption(
        "Upload the PPTX file (converted from merged PDF via Canva). "
        "NotebookLM branding will be automatically removed."
    )

    uploaded_pptx = st.file_uploader(
        "Upload PPTX file",
        type=["pptx"],
        accept_multiple_files=False,
        key="pptx_cleaner",
    )

    if uploaded_pptx:
        st.caption(f"Uploaded: {uploaded_pptx.name}")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("Remove Logo", type="primary"):
                progress_box = st.empty()
                with st.spinner("Removing NotebookLM branding..."):
                    try:
                        pptx_bytes = uploaded_pptx.read()
                        file_size_kb = len(pptx_bytes) // 1024

                        # Diagnostic scan
                        diag = _diagnose_pptx(pptx_bytes)
                        st.session_state['pptx_diagnostic'] = diag

                        progress_box.info(f"Processing {file_size_kb} KB PPTX file...")

                        # Run logo removal
                        clean_bytes, logos_removed = _remove_notebooklm_logo(
                            pptx_bytes, progress_container=progress_box
                        )

                        import io
                        from pptx import Presentation
                        prs = Presentation(io.BytesIO(clean_bytes))
                        total_slides = len(prs.slides)

                        # Verify images were actually modified
                        import zipfile
                        from PIL import Image
                        orig_z = zipfile.ZipFile(io.BytesIO(pptx_bytes), 'r')
                        clean_z = zipfile.ZipFile(io.BytesIO(clean_bytes), 'r')
                        changed = 0
                        for name in orig_z.namelist():
                            if 'ppt/media/' in name.lower():
                                orig_data = orig_z.read(name)
                                clean_data = clean_z.read(name)
                                if orig_data != clean_data:
                                    changed += 1
                        orig_z.close()
                        clean_z.close()

                        progress_box.empty()
                        st.success(
                            f"**{total_slides} slides** | "
                            f"Processed {logos_removed} elements | "
                            f"**{changed} images modified**"
                        )

                        if changed == 0:
                            st.warning(
                                "No images were modified. This may indicate the logo "
                                "removal function could not process the images. "
                                "Check the diagnostic info below."
                            )

                        course_name = st.session_state.get('extracted_course_info', {}).get('Course_Title', 'Slides')
                        safe_name = re.sub(r'[^\w\s\-]', '', course_name).strip().replace(' ', '_')[:50]
                        clean_filename = f"{safe_name}_clean.pptx"

                        st.download_button(
                            label=f"Download Clean PPTX ({total_slides} slides)",
                            data=clean_bytes,
                            file_name=clean_filename,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            type="primary",
                        )
                    except Exception as e:
                        progress_box.empty()
                        st.error(f"Error removing logo: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                        logger.exception("Logo removal error")

        # Show diagnostic info if available
        diag = st.session_state.get('pptx_diagnostic')
        if diag:
            with st.expander("PPTX Diagnostic Info"):
                st.text(diag)
