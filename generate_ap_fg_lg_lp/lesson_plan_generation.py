"""
Lesson Plan Generation - Standalone Streamlit Page

Generates a Lesson Plan (LP) document from a Course Proposal upload.
Features an editable prompt template for the timetable generation.
"""

import streamlit as st
import asyncio
import os
import pandas as pd

from generate_ap_fg_lg_lp.courseware_generation import parse_cp_document, interpret_cp
from generate_ap_fg_lg_lp.utils.timetable_generator import extract_unique_instructional_methods
from generate_ap_fg_lg_lp.utils.agentic_LP import generate_lesson_plan
from generate_ap_fg_lg_lp.utils.organizations import get_organizations
from anthropic import Anthropic
from utils.claude_model_client import get_claude_model_id
from utils.helpers import parse_json_content
from datetime import datetime


# =============================================================================
# Default Prompt Template
# =============================================================================

DEFAULT_LP_PROMPT = """You are a WSQ timetable generator. Create a lesson plan for {num_of_days} day(s), 0930-1830hrs daily.

**RULES:**
1. Use ONLY these instructional methods: {list_of_im}
2. Resources: "Slide page #", "TV", "Whiteboard", "Wi-Fi"
3. Include ALL topics and bullet points from the course

**FIXED SESSIONS:**
- Day 1 Start: 0930-0945 (15min) - "Digital Attendance and Introduction" (N/A)
- Other Days Start: 0930-0940 (10min) - "Digital Attendance (AM)" (N/A)
- Morning Break: 1050-1100 (10min)
- Lunch: 1200-1245 (45min)
- PM Attendance: 1330-1340 (10min) - "Digital Attendance (PM)" (N/A)
- Afternoon Break: 1500-1510 (10min)
- End of Day: 1810-1830 (20min) - "Recap All Contents and Close" or "Course Feedback and TRAQOM Survey" (last day)

**FINAL DAY ASSESSMENTS** (schedule at end):
- Digital Attendance (Assessment) - 10min
- Final Assessment sessions (use Assessment_Methods_Details for durations)
- Course Feedback and TRAQOM Survey - 1810-1830

**SESSION FORMAT:**
- Topic: instruction_title="Topic X: [Title] (K#, A#)", bullet_points=[list of points]
- Activity: instruction_title="Activity: [Description]", bullet_points=[] (empty)

**OUTPUT JSON:**
{{"lesson_plan": [{{"Day": "Day 1", "Sessions": [{{"Time": "0930hrs - 0945hrs (15 mins)", "instruction_title": "...", "bullet_points": [...], "Instructional_Methods": "...", "Resources": "..."}}]}}]}}"""


# =============================================================================
# Timetable Generation (with custom prompt support)
# =============================================================================

async def generate_timetable_with_prompt(context, num_of_days, system_prompt, model_choice="default"):
    """Generate timetable using a custom system prompt."""
    model_id = get_claude_model_id(model_choice)
    client = Anthropic()

    agent_task = f"""
        1. Take the complete dictionary provided:
        {context}
        2. Use the provided JSON dictionary, which includes all the course information, to generate the lesson plan timetable.

        **Instructions:**
        1. Adhere to all the rules and guidelines.
        2. Include the timetable data under the key 'lesson_plan' within a JSON dictionary.
        3. Return the JSON dictionary containing the 'lesson_plan' key.
    """

    max_retries = 2
    base_delay = 5

    for attempt in range(max_retries):
        try:
            completion = client.messages.create(
                model=model_id,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": agent_task}],
                max_tokens=8192
            )
            break
        except Exception as e:
            error_str = str(e)
            if "overloaded" in error_str.lower() or "529" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"Model overloaded after {max_retries} attempts.")
            else:
                raise e

    response_text = completion.content[0].text
    result = parse_json_content(response_text)

    if not result or 'lesson_plan' not in result:
        raise Exception("Generated timetable is missing 'lesson_plan' key.")

    return result


# =============================================================================
# Preview Helper
# =============================================================================

def display_timetable_preview(lesson_plan):
    """Display generated timetable as day-by-day expanders."""
    for day_data in lesson_plan:
        day_label = day_data.get("Day", "Day")
        sessions = day_data.get("Sessions", [])

        with st.expander(f"{day_label} ({len(sessions)} sessions)", expanded=False):
            rows = []
            for s in sessions:
                rows.append({
                    "Time": s.get("Time", ""),
                    "Topic / Activity": s.get("instruction_title", ""),
                    "Methods": s.get("Instructional_Methods", ""),
                    "Resources": s.get("Resources", ""),
                })
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)


# =============================================================================
# Main App
# =============================================================================

def app():
    st.title("Generate Lesson Plan")

    # Get organizations for company selection
    organizations = get_organizations()
    selected_company = st.session_state.get('selected_company', {})
    selected_org = selected_company.get('name', '')

    # ----- Step 1: Upload Course Proposal -----
    st.subheader("Step 1: Upload Course Proposal")
    st.write("Upload your Course Proposal (.docx or .xlsx) to generate a Lesson Plan.")
    cp_file = st.file_uploader("Upload Course Proposal", type=["docx", "xlsx"], key="lp_cp_upload")

    # ----- Step 2: Prompt Template -----
    st.subheader("Step 2: Prompt Template")
    st.write("Customize the timetable generation prompt below. The placeholders `{num_of_days}` and `{list_of_im}` will be auto-filled from your Course Proposal.")

    if 'lp_prompt_template' not in st.session_state:
        st.session_state['lp_prompt_template'] = DEFAULT_LP_PROMPT

    prompt_template = st.text_area(
        "Timetable Generation Prompt:",
        value=st.session_state['lp_prompt_template'],
        height=400,
        key="lp_prompt_editor"
    )
    st.session_state['lp_prompt_template'] = prompt_template

    # ----- Step 3: Generate -----
    st.subheader("Step 3: Generate Lesson Plan")

    if st.button("Generate Lesson Plan", type="primary"):
        if cp_file is None:
            st.error("Please upload a Course Proposal document.")
            return
        if not selected_org:
            st.error("Please select a company from the sidebar.")
            return

        model_choice = st.session_state.get('selected_model', 'default')

        # Parse CP
        try:
            with st.spinner("Parsing Course Proposal..."):
                raw_data = parse_cp_document(cp_file)
        except Exception as e:
            st.error(f"Error parsing Course Proposal: {e}")
            return

        # Interpret CP with Claude
        try:
            with st.spinner("Extracting information from Course Proposal..."):
                context = asyncio.run(interpret_cp(raw_data=raw_data, model_choice=model_choice))
        except Exception as e:
            st.error(f"Error extracting Course Proposal: {e}")
            return

        if not context:
            st.error("Failed to extract course data. Please check the document format.")
            return

        # Add metadata
        current_datetime = datetime.now()
        context["Date"] = current_datetime.strftime("%d %b %Y")
        context["Year"] = current_datetime.year

        # Get organization UEN
        org_list = get_organizations()
        selected_org_data = next((org for org in org_list if org["name"] == selected_org), None)
        if selected_org_data:
            context["UEN"] = selected_org_data["uen"]

        # Calculate days
        duration_str = context.get("Total_Course_Duration_Hours", "")
        if not duration_str:
            duration_str = context.get("Total_Training_Hours", "") or context.get("Total_Course_Duration", "") or "16 hrs"
        hours = int(''.join(filter(str.isdigit, str(duration_str))) or "16")
        num_of_days = hours / 8

        # Build the final prompt from template
        list_of_im = extract_unique_instructional_methods(context)
        final_prompt = prompt_template.replace("{num_of_days}", str(int(num_of_days)))
        final_prompt = final_prompt.replace("{list_of_im}", str(list_of_im))

        # Generate timetable
        try:
            with st.spinner("Generating timetable schedule..."):
                timetable_data = asyncio.run(
                    generate_timetable_with_prompt(context, num_of_days, final_prompt, model_choice)
                )
                context['lesson_plan'] = timetable_data['lesson_plan']
        except Exception as e:
            st.error(f"Error generating timetable: {e}")
            return

        # Generate LP document
        try:
            with st.spinner("Generating Lesson Plan document..."):
                lp_output = generate_lesson_plan(context, selected_org)
        except Exception as e:
            st.error(f"Error generating Lesson Plan: {e}")
            return

        if lp_output:
            st.success("Lesson Plan generated successfully!")
            st.session_state['lp_standalone_output'] = lp_output
            st.session_state['lp_timetable'] = timetable_data['lesson_plan']
            st.session_state['lp_context'] = context

    # ----- Preview -----
    if st.session_state.get('lp_timetable'):
        st.subheader("Timetable Preview")
        display_timetable_preview(st.session_state['lp_timetable'])

    # ----- Download -----
    if st.session_state.get('lp_standalone_output'):
        lp_path = st.session_state['lp_standalone_output']
        if os.path.exists(lp_path):
            ctx = st.session_state.get('lp_context', {})
            course_title = ctx.get('Course_Title', 'Course')
            # Sanitize filename
            safe_title = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in str(course_title))[:50].strip('_')

            with open(lp_path, "rb") as f:
                st.download_button(
                    label="Download Lesson Plan (.docx)",
                    data=f.read(),
                    file_name=f"LP_{safe_title}_v1.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
