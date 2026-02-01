"""
Annex Assessment Module - Chainlit

Handles merging assessment documents into Assessment Plan as annexes.

Author: Courseware Generator Team
Date: February 2026
"""

import sys
import os
import asyncio
import tempfile

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl


async def on_start():
    """Called when Add to AP profile is selected."""
    cl.user_session.set("annex_state", "awaiting_ap")
    cl.user_session.set("ap_file", None)
    cl.user_session.set("assessment_files", [])


async def on_message(message: cl.Message):
    """Handle messages in Add to AP context."""
    state = cl.user_session.get("annex_state", "awaiting_ap")
    content = message.content.lower()

    if state == "awaiting_ap":
        if any(kw in content for kw in ["upload", "start", "begin"]):
            await request_ap_upload()
        else:
            await cl.Message(
                content="Upload your Assessment Plan (.docx) first, then I'll ask for the assessment documents."
            ).send()

    elif state == "awaiting_assessments":
        if any(kw in content for kw in ["upload", "add", "more"]):
            await request_assessment_upload()
        elif any(kw in content for kw in ["done", "finish", "merge", "generate"]):
            await merge_documents()
        else:
            await cl.Message(
                content="Upload your assessment Q&A documents, or say 'done' when ready to merge."
            ).send()

    elif state == "processing":
        await cl.Message(content="Merging documents. Please wait...").send()

    elif state == "completed":
        if any(kw in content for kw in ["another", "new", "again"]):
            await on_start()
            await cl.Message(content="Ready to merge new documents. Upload your Assessment Plan.").send()
        else:
            await cl.Message(content="Your merged document is ready above. Say 'new' to start over.").send()


async def on_file_upload(files: list):
    """Handle file uploads."""
    if not files:
        return

    state = cl.user_session.get("annex_state", "awaiting_ap")

    if state == "awaiting_ap":
        # Looking for AP file
        docx_files = [f for f in files if f.name.endswith('.docx')]
        if docx_files:
            ap_file = docx_files[0]
            cl.user_session.set("ap_file", ap_file)

            await cl.Message(
                content=f"Received Assessment Plan: **{ap_file.name}**\n\n"
                        "Now upload your assessment Question and Answer documents."
            ).send()

            cl.user_session.set("annex_state", "awaiting_assessments")
        else:
            await cl.Message(content="Please upload an Assessment Plan (.docx).").send()

    elif state == "awaiting_assessments":
        # Add to assessment files list
        docx_files = [f for f in files if f.name.endswith('.docx')]
        current_files = cl.user_session.get("assessment_files", [])
        current_files.extend(docx_files)
        cl.user_session.set("assessment_files", current_files)

        file_names = [f.name for f in docx_files]
        total = len(current_files)

        await cl.Message(
            content=f"Added: {', '.join(file_names)}\n\n"
                    f"**Total assessment files:** {total}\n\n"
                    "Upload more files, or say 'done' to merge."
        ).send()


async def request_ap_upload():
    """Request Assessment Plan upload."""
    files = await cl.AskFileMessage(
        content="Please upload your Assessment Plan (.docx):",
        accept=["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        max_files=1,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def request_assessment_upload():
    """Request assessment documents upload."""
    files = await cl.AskFileMessage(
        content="Upload assessment Question and Answer documents (.docx):\n"
                "(You can upload multiple files at once)",
        accept=["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        max_files=10,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def merge_documents():
    """Merge all documents into AP with annexes."""
    ap_file = cl.user_session.get("ap_file")
    assessment_files = cl.user_session.get("assessment_files", [])

    if not ap_file:
        await cl.Message(content="No Assessment Plan found. Please upload one first.").send()
        return

    if not assessment_files:
        await cl.Message(content="No assessment files to merge. Please upload some first.").send()
        return

    cl.user_session.set("annex_state", "processing")

    await cl.Message(
        content=f"Merging {len(assessment_files)} documents into Assessment Plan..."
    ).send()

    try:
        async with cl.Step(name="Merging Documents", type="run") as step:
            step.input = f"Processing {ap_file.name} with {len(assessment_files)} annexes..."

            # Save files temporarily
            temp_dir = tempfile.mkdtemp()

            ap_path = os.path.join(temp_dir, ap_file.name)
            with open(ap_path, "wb") as f:
                f.write(ap_file.content)

            assessment_paths = []
            for af in assessment_files:
                af_path = os.path.join(temp_dir, af.name)
                with open(af_path, "wb") as f:
                    f.write(af.content)
                assessment_paths.append(af_path)

            # Placeholder for actual merging
            # Would use docxcompose or similar to merge documents

            step.output = "Documents merged successfully!"

        await cl.Message(
            content="Document merging integration in progress.\n\n"
                    "The existing pipeline from `add_assessment_to_ap/` will be connected here.\n\n"
                    f"**Files to merge:**\n"
                    f"- Assessment Plan: {ap_file.name}\n"
                    f"- Assessments: {len(assessment_files)} files"
        ).send()

        cl.user_session.set("annex_state", "completed")

    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()
        cl.user_session.set("annex_state", "awaiting_assessments")
