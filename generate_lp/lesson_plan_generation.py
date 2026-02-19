"""
Lesson Plan Generation - Streamlit Page

Generates lesson plans using pure Python barrier algorithm.
No AI agents needed - instant schedule generation.
"""

import streamlit as st
import os
import pandas as pd

from generate_ap_fg_lg.courseware_generation import apply_tsc_defaults
from generate_lp.timetable_generator import (
    build_lesson_plan_schedule,
    generate_lesson_plan_docx,
)
from utils.helpers import copy_to_courseware


# =============================================================================
# Preview Helper
# =============================================================================

def display_timetable_preview(schedule_data: dict):
    """Display generated schedule as day-by-day expanders with tables."""
    days = schedule_data.get("days", {})
    for day_num in sorted(days.keys()):
        slots = days[day_num]
        with st.expander(f"Day {day_num}", expanded=False):
            rows = []
            for s in slots:
                slot_lu = s.get("lu_num")
                if slot_lu:
                    is_contd = s.get("is_contd", False)
                    header = f"LU{slot_lu}: {s.get('lu_title', '')}"
                    if is_contd:
                        header += " (Cont'd)"
                    rows.append({
                        "Timing": "",
                        "Duration": "",
                        "Description": f"**{header}**",
                        "Methods": "",
                    })
                # Replace newlines with " | " for flat table display
                desc = s.get("description", "").replace("\n", " | ")
                rows.append({
                    "Timing": s.get("timing", ""),
                    "Duration": s.get("duration", ""),
                    "Description": desc,
                    "Methods": s.get("methods", ""),
                })
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)


# =============================================================================
# Main App
# =============================================================================

def app():
    st.title("Generate Lesson Plan")

    # Get organization from sidebar
    selected_company = st.session_state.get('selected_company', {})

    # Auto-load from Extract Course Info session state
    extracted_info = st.session_state.get('extracted_course_info')
    if extracted_info and not st.session_state.get('lp_context'):
        context = apply_tsc_defaults(dict(extracted_info))
        st.session_state['lp_context'] = context

    # ----- Course Info Status -----
    from utils.agent_runner import get_job
    extract_job = get_job("extract_course_info")
    if extract_job and extract_job.get("status") == "running":
        st.info("Course info extraction is still running. Please wait for it to complete.")
    elif st.session_state.get('lp_context'):
        ctx = st.session_state['lp_context']
        course_title = ctx.get('Course_Title', 'N/A')
        num_topics = sum(len(lu.get('Topics', [])) for lu in ctx.get('Learning_Units', []))
        duration = ctx.get('Total_Course_Duration_Hours', 'N/A')
        st.success(f"**{course_title}** | {num_topics} topic(s) | {duration}")
    else:
        st.warning("No course info loaded. Please extract course info first.")

    # ----- Generate Lesson Plan -----
    if st.button("Generate Lesson Plan", type="primary"):
        context = st.session_state.get('lp_context')
        if context is None:
            st.error("Please extract course info first.")
        elif extract_job and extract_job.get("status") == "running":
            st.warning("Please wait for course info extraction to complete.")
        else:
            with st.spinner("Generating lesson plan..."):
                # Build schedule (instant - pure Python)
                schedule_data = build_lesson_plan_schedule(context)
                st.session_state['lp_schedule'] = schedule_data

                # Generate DOCX
                try:
                    docx_path = generate_lesson_plan_docx(context, schedule_data, selected_company)
                    st.session_state['lp_docx_path'] = docx_path
                except Exception as e:
                    st.error(f"Error generating DOCX: {e}")

            st.success("Lesson plan generated!")
            st.rerun()

    # ----- Preview -----
    if st.session_state.get('lp_schedule'):
        schedule = st.session_state['lp_schedule']

        st.caption(
            f"{schedule.get('num_days', 1)} day(s) | "
            f"{schedule.get('per_topic_mins', 0)} mins per topic | "
            f"{schedule.get('instructional_hours', 0)} hrs instruction | "
            f"{schedule.get('assessment_hours', 0)} hrs assessment"
        )

        display_timetable_preview(schedule)

    # ----- Download -----
    if st.session_state.get('lp_docx_path'):
        docx_path = st.session_state['lp_docx_path']
        if os.path.exists(docx_path):
            ctx = st.session_state.get('lp_context', {})
            course_title = ctx.get('Course_Title', 'Course')
            tgs_ref = ctx.get('TGS_Ref_No', '')
            safe_title = ''.join(
                c if c.isalnum() or c in (' ', '_', '-') else '_'
                for c in str(course_title)
            )[:50].strip('_')
            safe_tgs = ''.join(
                c if c.isalnum() or c in ('-', '_') else '_'
                for c in str(tgs_ref)
            ).strip('_')

            if safe_tgs:
                lp_filename = f"LP_{safe_tgs}_{safe_title}_v1.docx"
            else:
                lp_filename = f"LP_{safe_title}_v1.docx"

            # Copy to Courseware/Lesson Plan folder
            copy_to_courseware(docx_path, "Lesson Plan", lp_filename, ctx)

            with open(docx_path, "rb") as f:
                st.download_button(
                    label="Download Lesson Plan (.docx)",
                    data=f.read(),
                    file_name=lp_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
