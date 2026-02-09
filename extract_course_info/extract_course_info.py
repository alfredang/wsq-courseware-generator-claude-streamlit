"""
Extract Course Info - Standalone Streamlit Page

Uploads an approved Course Proposal (CP) and extracts key course information
for display and reuse by other generation modules.
"""

import streamlit as st
import asyncio
import os
import tempfile
import pandas as pd

from generate_ap_fg_lg.courseware_generation import parse_cp_document
from courseware_agents.cp_interpreter import interpret_cp


def display_course_info(context):
    """Display extracted course information in organized sections."""

    # --- Course Overview ---
    st.subheader("Course Overview")
    overview_data = [
        {"Field": "Course Title", "Value": context.get('Course_Title', 'N/A')},
        {"Field": "Course Ref Code (TGS)", "Value": context.get('TGS_Ref_No', 'N/A')},
        {"Field": "TSC Code", "Value": context.get('TSC_Code', 'N/A')},
        {"Field": "TSC Title", "Value": context.get('TSC_Title', 'N/A')},
        {"Field": "Skills Framework", "Value": context.get('Skills_Framework', 'N/A')},
        {"Field": "Sector", "Value": context.get('TSC_Sector', 'N/A')},
        {"Field": "Proficiency Level", "Value": context.get('Proficiency_Level', 'N/A')},
        {"Field": "Total Course Duration", "Value": context.get('Total_Course_Duration_Hours', 'N/A')},
        {"Field": "Total Training Hours", "Value": context.get('Total_Training_Hours', 'N/A')},
        {"Field": "Total Assessment Hours", "Value": context.get('Total_Assessment_Hours', 'N/A')},
        {"Field": "Course Fee", "Value": context.get('Course_Fee', 'N/A')},
    ]
    df_overview = pd.DataFrame(overview_data)
    st.dataframe(df_overview, use_container_width=True, hide_index=True)

    st.divider()

    # --- What This Course Is About ---
    st.subheader("What This Course Is About")
    description = context.get('TSC_Description') or context.get('Proficiency_Description') or 'N/A'
    st.write(description)

    st.divider()

    # --- What You'll Learn (Learning Outcomes) ---
    st.subheader("What You'll Learn")
    learning_units = context.get('Learning_Units', [])
    if learning_units:
        for lu in learning_units:
            lo = lu.get('LO', '')
            if lo:
                st.markdown(f"- {lo}")
    else:
        st.write("No learning outcomes found.")

    st.divider()

    # --- Topics ---
    st.subheader("Topics")
    if learning_units:
        for lu in learning_units:
            lu_title = lu.get('LU_Title', 'Learning Unit')
            with st.expander(lu_title, expanded=False):
                topics = lu.get('Topics', [])
                for topic in topics:
                    topic_title = topic.get('Topic_Title', '')
                    bullet_points = topic.get('Bullet_Points', [])
                    st.markdown(f"**{topic_title}**")
                    for bp in bullet_points:
                        st.markdown(f"  - {bp}")

                # K & A statements
                k_statements = lu.get('K_numbering_description', [])
                a_statements = lu.get('A_numbering_description', [])
                if k_statements:
                    st.markdown("**Knowledge Statements:**")
                    for k in k_statements:
                        st.markdown(f"  - **{k.get('K_number', '')}**: {k.get('Description', '')}")
                if a_statements:
                    st.markdown("**Ability Statements:**")
                    for a in a_statements:
                        st.markdown(f"  - **{a.get('A_number', '')}**: {a.get('Description', '')}")
    else:
        st.write("No topics found.")

    st.divider()

    # --- Instructional Methods & Duration ---
    st.subheader("Instructional Methods & Duration")
    if learning_units:
        im_rows = []
        for lu in learning_units:
            lu_title = lu.get('LU_Title', '')
            methods = lu.get('Instructional_Methods', [])
            if methods:
                im_rows.append({
                    "Learning Unit": lu_title,
                    "Instructional Methods": ", ".join(methods)
                })
        if im_rows:
            df_im = pd.DataFrame(im_rows)
            st.dataframe(df_im, use_container_width=True, hide_index=True)
        else:
            st.write("No instructional methods found.")
    else:
        st.write("No instructional methods found.")

    st.divider()

    # --- Assessment Methods & Duration ---
    st.subheader("Assessment Methods & Duration")
    assessment_details = context.get('Assessment_Methods_Details', [])
    if assessment_details:
        am_rows = []
        for am in assessment_details:
            am_rows.append({
                "Assessment Method": am.get('Assessment_Method', ''),
                "Abbreviation": am.get('Method_Abbreviation', ''),
                "Duration": am.get('Total_Delivery_Hours', ''),
                "Assessor:Candidate Ratio": ", ".join(am.get('Assessor_to_Candidate_Ratio', [])),
            })
        df_am = pd.DataFrame(am_rows)
        st.dataframe(df_am, use_container_width=True, hide_index=True)
    else:
        st.write("No assessment methods found.")


def app():
    st.title("Extract Course Info")
    st.write("Upload an approved Course Proposal to extract key course information.")

    # --- Upload ---
    cp_file = st.file_uploader(
        "Upload Course Proposal",
        type=["docx", "xlsx"],
        key="extract_cp_upload"
    )

    # --- Optional fields ---
    st.markdown("**Optional: Supplement missing info from external sources**")
    col1, col2 = st.columns(2)
    with col1:
        course_ref_code = st.text_input(
            "Course Ref Code (TGS)",
            placeholder="e.g. TGS-2024001234",
            key="extract_course_ref_code"
        )
    with col2:
        course_url = st.text_input(
            "Course URL",
            placeholder="e.g. https://www.myskillsfuture.gov.sg/...",
            key="extract_course_url"
        )

    # --- Extract ---
    from utils.agent_runner import submit_agent_job, get_job
    from utils.agent_status import render_page_job_status

    if st.button("Extract Course Info", type="primary"):
        if cp_file is None:
            st.error("Please upload a Course Proposal document.")
        else:
            # Parse CP (fast, synchronous)
            try:
                with st.spinner("Parsing Course Proposal..."):
                    raw_data = parse_cp_document(cp_file)
            except Exception as e:
                st.error(f"Error parsing Course Proposal: {e}")
                raw_data = None

            if raw_data:
                # Save parsed text to temp file for the agent
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
                    tmp.write(raw_data)
                    parsed_cp_path = tmp.name
                st.session_state['_extract_cp_temp_path'] = parsed_cp_path

                # Submit background agent job
                job = submit_agent_job(
                    key="extract_course_info",
                    label="Extract Course Info",
                    async_fn=interpret_cp,
                    kwargs={
                        "parsed_cp_path": parsed_cp_path,
                        "course_ref_code": course_ref_code or None,
                        "course_url": course_url or None,
                    },
                )

                if job is None:
                    st.warning("Course info extraction is already running.")
                else:
                    st.rerun()

    # --- Agent Status ---
    def _on_extract_complete(job):
        result = job["result"]
        if result:
            st.session_state['extracted_course_info'] = result
        # Clean up temp file
        temp_path = st.session_state.pop('_extract_cp_temp_path', None)
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

    job_status = render_page_job_status(
        "extract_course_info",
        on_complete=_on_extract_complete,
        running_message="AI Agent extracting course information... (approximately 40-60 seconds)",
    )

    if job_status == "running":
        st.stop()

    # --- Display Results ---
    if st.session_state.get('extracted_course_info'):
        st.divider()
        display_course_info(st.session_state['extracted_course_info'])

        # Collapsible JSON context
        with st.expander("Course Context JSON", expanded=False):
            st.json(st.session_state['extracted_course_info'])
