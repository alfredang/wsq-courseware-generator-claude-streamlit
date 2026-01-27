"""
File: slides_generation.py

===============================================================================
Slides Generation Module
===============================================================================
Description:
    This module generates PowerPoint presentation slides from course materials
    using NotebookLM MCP for AI-powered content processing.

Main Functionalities:
    - Upload course materials (Facilitator Guide, Learner Guide, Course Proposal)
    - Create NotebookLM notebooks for content processing
    - Generate presentation slides using AI
    - Download slides in presentation format

Dependencies:
    - streamlit
    - NotebookLM MCP (external service)

Author:
    WSQ Courseware Assistant
Date:
    January 2025
===============================================================================
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


def extract_text_from_file(uploaded_file) -> str:
    """
    Extract text content from uploaded file.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        str: Extracted text content
    """
    try:
        file_extension = Path(uploaded_file.name).suffix.lower()

        if file_extension == '.txt':
            return uploaded_file.read().decode('utf-8')

        elif file_extension == '.pdf':
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                st.warning("PyPDF2 not installed. Please install it to read PDF files.")
                return ""

        elif file_extension in ['.docx', '.doc']:
            try:
                from docx import Document
                doc = Document(uploaded_file)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except ImportError:
                st.warning("python-docx not installed. Please install it to read Word documents.")
                return ""

        else:
            # Try to read as text
            try:
                return uploaded_file.read().decode('utf-8')
            except:
                st.error(f"Unsupported file type: {file_extension}")
                return ""

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""


def check_mcp_available() -> bool:
    """
    Check if NotebookLM MCP server is available.

    Returns:
        bool: True if MCP is available, False otherwise
    """
    # For now, return True - actual MCP integration will be done later
    # In production, this would check if the MCP server is running
    return True


def create_notebook_via_mcp(title: str) -> Optional[str]:
    """
    Create a new notebook via NotebookLM MCP.

    Args:
        title: Title for the notebook

    Returns:
        str: Notebook ID if successful, None otherwise
    """
    # Placeholder for MCP integration
    # This will be implemented when MCP server is connected
    st.info("NotebookLM MCP integration pending. Please configure MCP server.")
    return None


def add_source_to_notebook(notebook_id: str, content: str, title: str) -> bool:
    """
    Add source content to a notebook via MCP.

    Args:
        notebook_id: ID of the notebook
        content: Text content to add
        title: Title for the source

    Returns:
        bool: True if successful, False otherwise
    """
    # Placeholder for MCP integration
    return False


def generate_slides_via_mcp(notebook_id: str) -> Optional[Dict[str, Any]]:
    """
    Generate slide deck from notebook content via MCP.

    Args:
        notebook_id: ID of the notebook

    Returns:
        dict: Slide deck data if successful, None otherwise
    """
    # Placeholder for MCP integration
    return None


def app():
    """
    Streamlit web interface for Slides Generation.
    """
    st.title("Generate Slides")
    st.markdown("Generate professional presentation slides from course materials using NotebookLM")

    st.divider()

    # Check MCP availability
    mcp_available = check_mcp_available()

    if not mcp_available:
        st.warning("""
        **NotebookLM MCP Server Not Connected**

        To use this feature, please ensure the NotebookLM MCP server is running.
        See: https://github.com/alfredang/notebooklm-mcp
        """)

    # File Upload Section
    st.subheader("1. Upload Course Materials")

    col1, col2 = st.columns(2)

    with col1:
        material_type = st.selectbox(
            "Select Material Type:",
            ["Facilitator Guide (FG)", "Learner Guide (LG)", "Course Proposal (CP)", "Other Document"],
            help="Choose the type of course material you're uploading"
        )

    with col2:
        output_format = st.selectbox(
            "Output Format:",
            ["PowerPoint (PPTX)", "PDF Slides", "Google Slides"],
            help="Choose the output format for your slides"
        )

    uploaded_file = st.file_uploader(
        "Upload your course material:",
        type=['pdf', 'docx', 'doc', 'txt'],
        help="Supported formats: PDF, Word documents (.docx, .doc), Text files (.txt)"
    )

    st.divider()

    # Configuration Section
    st.subheader("2. Slide Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        slides_per_topic = st.number_input(
            "Slides per Topic:",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of slides to generate per topic/learning unit"
        )

    with col2:
        include_notes = st.checkbox(
            "Include Speaker Notes",
            value=True,
            help="Add facilitator notes to each slide"
        )

    with col3:
        include_summaries = st.checkbox(
            "Include Section Summaries",
            value=True,
            help="Add summary slides at the end of each section"
        )

    # Additional options
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            slide_style = st.selectbox(
                "Slide Style:",
                ["Professional", "Modern", "Minimal", "Educational"],
                help="Choose the visual style for your slides"
            )

            color_scheme = st.selectbox(
                "Color Scheme:",
                ["Blue Professional", "Green Fresh", "Orange Warm", "Purple Creative", "Custom"],
                help="Choose the color scheme for your slides"
            )

        with col2:
            include_objectives = st.checkbox(
                "Include Learning Objectives Slide",
                value=True,
                help="Add a slide listing learning objectives"
            )

            include_assessment = st.checkbox(
                "Include Assessment Reminders",
                value=True,
                help="Add reminders about assessment points"
            )

    st.divider()

    # Preview Section (when file is uploaded)
    if uploaded_file:
        st.subheader("3. Content Preview")

        # Extract and preview content
        content = extract_text_from_file(uploaded_file)

        if content:
            with st.expander("Preview Extracted Content", expanded=False):
                st.text_area(
                    "Extracted Text (first 2000 characters):",
                    value=content[:2000] + ("..." if len(content) > 2000 else ""),
                    height=200,
                    disabled=True
                )

            st.success(f"File loaded successfully. Extracted {len(content)} characters of text.")

            # Store content in session state
            st.session_state['slides_content'] = content
            st.session_state['slides_filename'] = uploaded_file.name
        else:
            st.error("Could not extract content from the uploaded file.")

    st.divider()

    # Generation Section
    st.subheader("4. Generate Slides")

    generate_enabled = uploaded_file is not None and 'slides_content' in st.session_state

    if st.button("Generate Presentation Slides", type="primary", disabled=not generate_enabled):
        if not generate_enabled:
            st.error("Please upload a course material file first.")
            return

        content = st.session_state.get('slides_content', '')
        filename = st.session_state.get('slides_filename', 'course_material')

        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("Processing course material..."):
            # Step 1: Process content
            status_text.text("Step 1/4: Analyzing course content...")
            progress_bar.progress(25)

            # Step 2: Create notebook (placeholder)
            status_text.text("Step 2/4: Creating NotebookLM notebook...")
            progress_bar.progress(50)

            # Note: Actual MCP integration would happen here
            # notebook_id = create_notebook_via_mcp(filename)

            # Step 3: Generate slides (placeholder)
            status_text.text("Step 3/4: Generating presentation slides...")
            progress_bar.progress(75)

            # slides_data = generate_slides_via_mcp(notebook_id)

            # Step 4: Prepare download
            status_text.text("Step 4/4: Preparing download...")
            progress_bar.progress(100)

            # Show completion message
            st.info("""
            **NotebookLM MCP Integration Required**

            To complete slide generation, the NotebookLM MCP server needs to be configured.

            **Setup Instructions:**
            1. Install NotebookLM MCP: `npx @anthropic-ai/notebooklm-mcp`
            2. Configure MCP server in Claude Code settings
            3. Run the MCP server before generating slides

            See: https://github.com/alfredang/notebooklm-mcp
            """)

        progress_bar.empty()
        status_text.empty()

    # Help section
    with st.expander("How to Use This Module"):
        st.markdown("""
        ### Steps to Generate Slides:

        1. **Upload Course Material**: Upload your Facilitator Guide, Learner Guide, or Course Proposal
        2. **Configure Options**: Choose slides per topic, include speaker notes, etc.
        3. **Generate**: Click "Generate Presentation Slides"
        4. **Download**: Download your slides in the selected format

        ### Tips for Best Results:

        - **Facilitator Guide**: Best for comprehensive slides with teaching notes
        - **Course Proposal**: Good for overview/summary presentations
        - **Learner Guide**: Best for student-focused presentations

        ### NotebookLM MCP Features:

        - `create_notebook` - Create a new notebook for course content
        - `add_source_url` - Import web content as source
        - `add_source_text` - Add text content directly
        - `generate_slide_deck` - Generate PowerPoint-style slides
        - `ask_notebook` - Query content for specific sections
        """)


if __name__ == "__main__":
    app()
