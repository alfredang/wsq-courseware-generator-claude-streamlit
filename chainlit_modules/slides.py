"""
Slides Module - Chainlit

Handles presentation slide generation via NotebookLM.

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
    """Called when Slides profile is selected."""
    cl.user_session.set("slides_state", "awaiting_file")
    cl.user_session.set("source_file", None)
    cl.user_session.set("enable_research", True)


async def on_message(message: cl.Message):
    """Handle messages in Slides context."""
    state = cl.user_session.get("slides_state", "awaiting_file")
    content = message.content.lower()

    if state == "awaiting_file":
        if any(kw in content for kw in ["upload", "start", "create", "generate"]):
            await request_file_upload()
        elif "research" in content:
            if "no" in content or "without" in content or "disable" in content:
                cl.user_session.set("enable_research", False)
                await cl.Message(content="Research disabled. Upload your course material.").send()
            else:
                cl.user_session.set("enable_research", True)
                await cl.Message(content="Research enabled. Upload your course material.").send()
            await request_file_upload()
        else:
            await cl.Message(
                content="Upload a course document (FG, LG, or PDF) to generate presentation slides."
            ).send()

    elif state == "processing":
        await cl.Message(content="Slide generation in progress. Please wait...").send()

    elif state == "completed":
        if any(kw in content for kw in ["another", "new", "again"]):
            await on_start()
            await cl.Message(content="Ready to create new slides. Upload your course material.").send()
        else:
            await cl.Message(content="Your slides link is above. Say 'new' to create more.").send()


async def on_file_upload(files: list):
    """Handle file uploads."""
    if not files:
        return

    # Accept DOCX, PDF, TXT
    valid_files = [f for f in files if f.name.endswith(('.docx', '.pdf', '.txt'))]

    if not valid_files:
        await cl.Message(content="Please upload a valid document (.docx, .pdf, or .txt).").send()
        return

    source_file = valid_files[0]
    cl.user_session.set("source_file", source_file)

    await cl.Message(content=f"Received: **{source_file.name}**").send()

    # Confirm and start generation
    enable_research = cl.user_session.get("enable_research", True)
    research_status = "enabled" if enable_research else "disabled"

    await cl.Message(
        content=f"Ready to generate slides from this document.\n\n"
                f"**Options:**\n"
                f"- Internet research: {research_status}\n\n"
                f"Starting slide generation via NotebookLM..."
    ).send()

    await generate_slides()


async def request_file_upload():
    """Request file upload from user."""
    files = await cl.AskFileMessage(
        content="Please upload your course material:\n"
                "- Facilitator Guide (.docx)\n"
                "- Learner Guide (.docx)\n"
                "- Course Proposal (.docx)\n"
                "- PDF document",
        accept=[
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/pdf",
            "text/plain"
        ],
        max_files=1,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def generate_slides():
    """Generate slides using NotebookLM."""
    source_file = cl.user_session.get("source_file")
    enable_research = cl.user_session.get("enable_research", True)

    cl.user_session.set("slides_state", "processing")

    try:
        async with cl.Step(name="Generating Slides", type="run") as step:
            step.input = f"Processing {source_file.name}..."

            # Save file temporarily
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, source_file.name)

            with open(file_path, "wb") as f:
                f.write(source_file.content)

            # Extract text content
            content = ""
            if source_file.name.endswith('.docx'):
                try:
                    from docx import Document
                    doc = Document(file_path)
                    content = "\n".join([p.text for p in doc.paragraphs])
                except Exception as e:
                    step.output = f"Error reading DOCX: {e}"
            elif source_file.name.endswith('.pdf'):
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    content = "\n".join([page.extract_text() for page in reader.pages])
                except Exception as e:
                    step.output = f"Error reading PDF: {e}"
            elif source_file.name.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            if not content:
                step.output = "No content extracted from document."
                await cl.Message(content="Could not extract content from the document.").send()
                cl.user_session.set("slides_state", "awaiting_file")
                return

            step.output = f"Extracted {len(content)} characters. Sending to NotebookLM..."

            # Placeholder for NotebookLM integration
            # Would use notebooklm-py library to create notebook and generate slides

            await cl.Message(
                content="Slide generation integration in progress.\n\n"
                        "The existing NotebookLM pipeline from `generate_slides/` will be connected here.\n\n"
                        "When complete, you'll receive a link to view your slides in NotebookLM."
            ).send()

        cl.user_session.set("slides_state", "completed")

    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()
        cl.user_session.set("slides_state", "awaiting_file")
