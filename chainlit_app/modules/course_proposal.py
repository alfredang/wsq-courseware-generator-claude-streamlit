"""
Course Proposal Module - Chainlit

Handles Course Proposal generation workflow:
1. Upload TSC document
2. Select output format (Excel/Word)
3. Process with existing pipeline
4. Provide download links

Author: Courseware Generator Team
Date: February 2026
"""

import sys
import os
import asyncio
import tempfile

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl


async def on_start():
    """Called when Course Proposal profile is selected."""
    # Profile-specific initialization
    cl.user_session.set("cp_state", "awaiting_file")
    cl.user_session.set("cp_type", None)
    cl.user_session.set("tsc_file", None)


async def on_message(message: cl.Message):
    """Handle messages in Course Proposal context."""
    state = cl.user_session.get("cp_state", "awaiting_file")
    content = message.content.lower()

    if state == "awaiting_file":
        # Check if user wants to upload
        if any(kw in content for kw in ["upload", "create", "generate", "start", "begin"]):
            await request_file_upload()
        elif any(kw in content for kw in ["excel", "new cp"]):
            cl.user_session.set("cp_type", "New CP")
            await cl.Message(content="Excel format selected. Please upload your TSC document.").send()
            await request_file_upload()
        elif any(kw in content for kw in ["word", "docx", "old cp"]):
            cl.user_session.set("cp_type", "Old CP")
            await cl.Message(content="Word format selected. Please upload your TSC document.").send()
            await request_file_upload()
        else:
            await cl.Message(
                content="I'm ready to help you create a Course Proposal. Upload your TSC document (.docx) to begin."
            ).send()

    elif state == "awaiting_format":
        # User is selecting format
        if "excel" in content or "new" in content:
            await on_format_selected("excel")
        elif "word" in content or "docx" in content or "old" in content:
            await on_format_selected("docx")
        else:
            await cl.Message(
                content="Please select a format:\n- **Excel** (New CP format)\n- **Word** (Old CP format)"
            ).send()

    elif state == "processing":
        await cl.Message(content="Processing is in progress. Please wait...").send()

    elif state == "completed":
        if any(kw in content for kw in ["another", "new", "again", "restart"]):
            await on_start()
            await cl.Message(content="Ready for a new Course Proposal. Upload your TSC document.").send()
        else:
            await cl.Message(
                content="Your Course Proposal is ready above. Say 'new' to create another one."
            ).send()


async def on_file_upload(files: list):
    """Handle file uploads."""
    if not files:
        return

    # Get the first DOCX file
    docx_files = [f for f in files if f.name.endswith('.docx')]

    if not docx_files:
        await cl.Message(
            content="Please upload a TSC document in .docx format."
        ).send()
        return

    tsc_file = docx_files[0]
    cl.user_session.set("tsc_file", tsc_file)

    await cl.Message(
        content=f"Received: **{tsc_file.name}**\n\nThis looks like a TSC document. Now let's select the output format."
    ).send()

    # Ask for format selection
    actions = [
        cl.Action(name="cp_excel_format", value="excel", label="Excel Format (New CP)"),
        cl.Action(name="cp_docx_format", value="docx", label="Word Format (Old CP)"),
    ]

    await cl.Message(
        content="Which format would you like for your Course Proposal?",
        actions=actions
    ).send()

    cl.user_session.set("cp_state", "awaiting_format")


async def request_file_upload():
    """Request file upload from user."""
    files = await cl.AskFileMessage(
        content="Please upload your TSC document (.docx):",
        accept=["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        max_files=1,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def on_format_selected(format_type: str):
    """Handle format selection."""
    if format_type == "excel":
        cl.user_session.set("cp_type", "New CP")
        format_name = "Excel"
    else:
        cl.user_session.set("cp_type", "Old CP")
        format_name = "Word"

    tsc_file = cl.user_session.get("tsc_file")

    if not tsc_file:
        await cl.Message(content="No TSC document found. Please upload one first.").send()
        cl.user_session.set("cp_state", "awaiting_file")
        await request_file_upload()
        return

    await cl.Message(content=f"Great! Generating Course Proposal in **{format_name}** format...").send()

    cl.user_session.set("cp_state", "processing")
    await process_course_proposal()


async def process_course_proposal():
    """Process the TSC document and generate Course Proposal."""
    tsc_file = cl.user_session.get("tsc_file")
    cp_type = cl.user_session.get("cp_type", "New CP")

    try:
        # Create step for progress indication
        async with cl.Step(name="Generating Course Proposal", type="run") as step:
            step.input = f"Processing {tsc_file.name}..."

            # Save uploaded file to temp location
            temp_dir = tempfile.mkdtemp()
            input_path = os.path.join(temp_dir, tsc_file.name)

            # Read file content and save
            with open(input_path, "wb") as f:
                f.write(tsc_file.content)

            # Import and run the existing pipeline
            try:
                from generate_cp.main import main

                # Create a mock session state for the pipeline
                import streamlit as st
                if not hasattr(st, 'session_state'):
                    st.session_state = {}
                st.session_state['cp_type'] = cp_type
                st.session_state['selected_model'] = "DeepSeek-Chat"  # Default model

                # Run the pipeline
                await main(input_path)

                step.output = "Course Proposal generated successfully!"

            except ImportError as e:
                step.output = f"Pipeline import error: {e}"
                await cl.Message(
                    content=f"Error importing pipeline: {e}\n\nPlease ensure all dependencies are installed."
                ).send()
                cl.user_session.set("cp_state", "awaiting_file")
                return

            except Exception as e:
                step.output = f"Processing error: {e}"
                await cl.Message(
                    content=f"Error during processing: {e}\n\nPlease try again or contact support."
                ).send()
                cl.user_session.set("cp_state", "awaiting_file")
                return

        # Collect output files
        output_files = []
        output_dir = os.path.join(project_root, "generate_cp", "output_docs")

        # Check for CP document
        cp_docx_path = os.path.join(output_dir, "CP_output.docx")
        if os.path.exists(cp_docx_path):
            output_files.append(cl.File(
                name="CP_output.docx",
                path=cp_docx_path,
                display="inline"
            ))

        # Check for Excel file (New CP only)
        if cp_type == "New CP":
            excel_path = os.path.join(output_dir, "CP_template_metadata_preserved.xlsx")
            if os.path.exists(excel_path):
                output_files.append(cl.File(
                    name="CP_Excel_output.xlsx",
                    path=excel_path,
                    display="inline"
                ))

        # Check for CV validation documents
        cv_docs = [
            "CP_validation_template_bernard_updated.docx",
            "CP_validation_template_dwight_updated.docx",
            "CP_validation_template_ferris_updated.docx",
        ]
        for cv_doc in cv_docs:
            cv_path = os.path.join(output_dir, cv_doc)
            if os.path.exists(cv_path):
                output_files.append(cl.File(
                    name=cv_doc,
                    path=cv_path,
                    display="inline"
                ))

        if output_files:
            await cl.Message(
                content="Your Course Proposal is ready! Download the files below:",
                elements=output_files
            ).send()

            # Summary
            file_list = "\n".join([f"- {f.name}" for f in output_files])
            await cl.Message(
                content=f"**Generated files:**\n{file_list}\n\nSay 'new' to create another Course Proposal."
            ).send()
        else:
            await cl.Message(
                content="Processing completed but no output files were found. Please check the pipeline logs."
            ).send()

        cl.user_session.set("cp_state", "completed")

    except Exception as e:
        await cl.Message(
            content=f"An unexpected error occurred: {e}\n\nPlease try again."
        ).send()
        cl.user_session.set("cp_state", "awaiting_file")
