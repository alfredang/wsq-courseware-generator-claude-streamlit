"""
Lesson Plan Generation - Standalone Streamlit Page

Generates a Lesson Plan (LP) document from a Course Proposal upload.
Uses Claude Agent SDK for AI-powered timetable generation.

Workflow:
1. Upload CP document → Parse to text (no AI needed)
2. Interpret CP with AI Agent → Get structured context
3. Generate timetable with AI Agent → Get lesson plan schedule
4. Fill LP template → Download
"""

import streamlit as st
import os
import json
import asyncio
import pandas as pd

from generate_ap_fg_lg_lp.courseware_generation import parse_cp_document, apply_tsc_defaults
from generate_ap_fg_lg_lp.utils.timetable_generator import extract_unique_instructional_methods
from generate_ap_fg_lg_lp.utils.agentic_LP import generate_lesson_plan
from generate_ap_fg_lg_lp.utils.organizations import get_organizations
from datetime import datetime


# =============================================================================
# Default Prompt Template (editable by user)
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

    # ----- Prompt Template (editable) -----
    if 'lp_prompt_template' not in st.session_state:
        st.session_state['lp_prompt_template'] = DEFAULT_LP_PROMPT

    with st.expander("Timetable Prompt Template (editable)", expanded=False):
        st.write("Customize the prompt used by the AI agent for timetable generation.")
        prompt_template = st.text_area(
            "Timetable Generation Prompt:",
            value=st.session_state['lp_prompt_template'],
            height=400,
            key="lp_prompt_editor"
        )
        st.session_state['lp_prompt_template'] = prompt_template

    # ----- Step 2: Interpret CP & Generate Timetable -----
    st.subheader("Step 2: Generate Timetable with AI Agent")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Parse CP & Generate Timetable", type="primary"):
            if cp_file is None:
                st.error("Please upload a Course Proposal document.")
                return
            if not selected_org:
                st.error("Please select a company from the sidebar.")
                return

            # Parse CP
            try:
                with st.spinner("Parsing Course Proposal..."):
                    raw_data = parse_cp_document(cp_file)
                os.makedirs("output", exist_ok=True)
                with open("output/parsed_cp.md", "w", encoding="utf-8") as f:
                    f.write(raw_data)
                st.success("CP parsed successfully.")
            except Exception as e:
                st.error(f"Error parsing CP: {e}")
                return

            # Interpret CP with agent
            try:
                with st.spinner("AI Agent interpreting Course Proposal... (30-60 seconds)"):
                    from courseware_agents.cp_interpreter import interpret_cp
                    context = asyncio.run(interpret_cp("output/parsed_cp.md"))
                    context = apply_tsc_defaults(context)
                st.success(f"Course data extracted: {context.get('Course_Title', 'Unknown')}")
            except Exception as e:
                st.error(f"Error interpreting CP: {e}")
                return

            # Generate timetable with agent
            try:
                with st.spinner("AI Agent generating timetable... (30-60 seconds)"):
                    from courseware_agents.timetable_agent import generate_timetable
                    timetable = asyncio.run(generate_timetable("output/context.json"))
                    context['lesson_plan'] = timetable.get('lesson_plan', timetable)
                    st.session_state['lp_context'] = context
                    st.session_state['lp_timetable'] = context['lesson_plan']
                st.success("Timetable generated successfully!")
            except Exception as e:
                st.error(f"Error generating timetable: {e}")
                return

    with col2:
        # Alternative: Load pre-generated context JSON
        context_json_file = st.file_uploader("Or load context JSON", type=["json"], key="lp_context_json_upload")
        if context_json_file:
            try:
                context = json.load(context_json_file)
                context = apply_tsc_defaults(context)
                st.session_state['lp_context'] = context
                if 'lesson_plan' in context:
                    st.session_state['lp_timetable'] = context['lesson_plan']
                    st.success(f"Context loaded with timetable: {context.get('Course_Title', 'Unknown')}")
                else:
                    st.warning("Context loaded but no `lesson_plan` key found.")
            except Exception as e:
                st.error(f"Error loading context JSON: {e}")

    # Also check for existing output/context.json
    if os.path.exists("output/context.json") and not st.session_state.get('lp_context'):
        if st.button("Load from output/context.json", key="lp_load_existing"):
            try:
                with open("output/context.json", "r", encoding="utf-8") as f:
                    context = json.load(f)
                context = apply_tsc_defaults(context)
                st.session_state['lp_context'] = context
                if 'lesson_plan' in context:
                    st.session_state['lp_timetable'] = context['lesson_plan']
                    st.success(f"Context loaded: {context.get('Course_Title', 'Unknown')}")
            except Exception as e:
                st.error(f"Error: {e}")

    # ----- Preview -----
    if st.session_state.get('lp_timetable'):
        st.subheader("Timetable Preview")
        display_timetable_preview(st.session_state['lp_timetable'])

    # ----- Step 3: Generate LP Document -----
    st.subheader("Step 3: Generate Lesson Plan Document")

    if st.button("Generate Lesson Plan Document"):
        context = st.session_state.get('lp_context')

        if context is None:
            st.error("Please generate or load a context first (Step 2).")
            return
        if 'lesson_plan' not in context:
            st.error("Context is missing the `lesson_plan`. Generate the timetable first.")
            return

        # Add metadata
        current_datetime = datetime.now()
        context["Date"] = current_datetime.strftime("%d %b %Y")
        context["Year"] = current_datetime.year

        org_list = get_organizations()
        selected_org_data = next((org for org in org_list if org["name"] == selected_org), None)
        if selected_org_data:
            context["UEN"] = selected_org_data["uen"]

        try:
            with st.spinner("Generating Lesson Plan document..."):
                lp_output = generate_lesson_plan(context, selected_org)
        except Exception as e:
            st.error(f"Error generating Lesson Plan: {e}")
            return

        if lp_output:
            st.success("Lesson Plan generated successfully!")
            st.session_state['lp_standalone_output'] = lp_output

    # ----- Download -----
    if st.session_state.get('lp_standalone_output'):
        lp_path = st.session_state['lp_standalone_output']
        if os.path.exists(lp_path):
            ctx = st.session_state.get('lp_context', {})
            course_title = ctx.get('Course_Title', 'Course')
            safe_title = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in str(course_title))[:50].strip('_')

            with open(lp_path, "rb") as f:
                st.download_button(
                    label="Download Lesson Plan (.docx)",
                    data=f.read(),
                    file_name=f"LP_{safe_title}_v1.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
