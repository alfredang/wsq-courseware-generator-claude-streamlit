"""
Extract Course Info - Standalone Streamlit Page

Uploads an approved Course Proposal (CP) and extracts key course information
for display and reuse by other generation modules.
"""

import streamlit as st
import asyncio
import pandas as pd

from generate_ap_fg_lg_lp.courseware_generation import parse_cp_document, interpret_cp


def display_course_info(context):
    """Display extracted course information in organized sections."""

    # --- Course Overview ---
    st.subheader("Course Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Course Title:** {context.get('Course_Title', 'N/A')}")
        st.markdown(f"**Course Ref Code (TGS):** {context.get('TGS_Ref_No', 'N/A')}")
        st.markdown(f"**TSC Code:** {context.get('TSC_Code', 'N/A')}")
        st.markdown(f"**TSC Title:** {context.get('TSC_Title', 'N/A')}")
    with col2:
        st.markdown(f"**Total Course Duration:** {context.get('Total_Course_Duration_Hours', 'N/A')}")
        st.markdown(f"**Total Training Hours:** {context.get('Total_Training_Hours', 'N/A')}")
        st.markdown(f"**Total Assessment Hours:** {context.get('Total_Assessment_Hours', 'N/A')}")
        st.markdown(f"**Proficiency Level:** {context.get('Proficiency_Level', 'N/A')}")

    st.markdown(f"**Skills Framework:** {context.get('Skills_Framework', 'N/A')}")
    st.markdown(f"**Sector:** {context.get('TSC_Sector', 'N/A')}")

    # --- Course Fee ---
    course_fee = context.get('Course_Fee', 'N/A')
    st.markdown(f"**Course Fee:** {course_fee}")

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

    # --- Extract ---
    if st.button("Extract Course Info", type="primary"):
        if cp_file is None:
            st.error("Please upload a Course Proposal document.")
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
            with st.spinner("Extracting course information..."):
                context = asyncio.run(interpret_cp(raw_data=raw_data, model_choice=model_choice))
        except Exception as e:
            st.error(f"Error extracting course information: {e}")
            return

        if not context:
            st.error("Failed to extract course data. Please check the document format.")
            return

        st.success("Course information extracted successfully!")
        st.session_state['extracted_course_info'] = context

    # --- Display Results ---
    if st.session_state.get('extracted_course_info'):
        st.divider()
        display_course_info(st.session_state['extracted_course_info'])
