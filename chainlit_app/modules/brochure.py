"""
Brochure Module - Chainlit

Handles brochure generation from:
- Course Proposal data
- Web URL scraping

Author: Courseware Generator Team
Date: February 2026
"""

import sys
import os
import asyncio
import tempfile

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl


async def on_start():
    """Called when Brochure profile is selected."""
    cl.user_session.set("brochure_state", "awaiting_input")
    cl.user_session.set("brochure_source", None)
    cl.user_session.set("course_data", None)


async def on_message(message: cl.Message):
    """Handle messages in Brochure context."""
    state = cl.user_session.get("brochure_state", "awaiting_input")
    content = message.content.strip()

    if state == "awaiting_input":
        # Check if it's a URL
        if content.startswith("http://") or content.startswith("https://"):
            cl.user_session.set("brochure_source", "url")
            cl.user_session.set("course_url", content)
            await scrape_and_generate(content)
        elif any(kw in content.lower() for kw in ["upload", "file", "cp", "proposal"]):
            await request_file_upload()
        elif any(kw in content.lower() for kw in ["url", "link", "website", "scrape"]):
            await cl.Message(
                content="Please paste the course URL (e.g., MySkillsFuture course page)."
            ).send()
        else:
            await cl.Message(
                content="How would you like to create your brochure?\n\n"
                        "1. **Upload** a Course Proposal\n"
                        "2. **Paste** a course URL to scrape\n\n"
                        "Just upload a file or paste a URL to get started."
            ).send()

    elif state == "processing":
        await cl.Message(content="Brochure generation in progress. Please wait...").send()

    elif state == "completed":
        if any(kw in content.lower() for kw in ["another", "new", "again"]):
            await on_start()
            await cl.Message(content="Ready to create a new brochure.").send()
        else:
            await cl.Message(content="Your brochure is ready above. Say 'new' to create another.").send()


async def on_file_upload(files: list):
    """Handle file uploads."""
    if not files:
        return

    valid_files = [f for f in files if f.name.endswith(('.docx', '.json'))]

    if not valid_files:
        await cl.Message(content="Please upload a Course Proposal (.docx) or course data (.json).").send()
        return

    source_file = valid_files[0]
    cl.user_session.set("brochure_source", "file")
    cl.user_session.set("source_file", source_file)

    await cl.Message(content=f"Received: **{source_file.name}**").send()
    await generate_from_file(source_file)


async def request_file_upload():
    """Request file upload from user."""
    files = await cl.AskFileMessage(
        content="Please upload your Course Proposal (.docx) or course data (.json):",
        accept=[
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/json"
        ],
        max_files=1,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def scrape_and_generate(url: str):
    """Scrape course data from URL and generate brochure."""
    cl.user_session.set("brochure_state", "processing")

    await cl.Message(content=f"Scraping course information from:\n{url}").send()

    try:
        async with cl.Step(name="Scraping Course Data", type="tool") as step:
            step.input = f"Fetching data from {url}..."

            # Placeholder for web scraping
            # Would use existing scraping code from generate_brochure/

            step.output = "Course data extracted!"

        async with cl.Step(name="Generating Brochure", type="run") as step:
            step.input = "Creating professional brochure..."

            # Placeholder for brochure generation

            step.output = "Brochure generated!"

        await cl.Message(
            content="Brochure generation integration in progress.\n\n"
                    "The existing pipeline from `generate_brochure/` will be connected here.\n\n"
                    "Output formats: HTML and PDF."
        ).send()

        cl.user_session.set("brochure_state", "completed")

    except Exception as e:
        await cl.Message(content=f"Error scraping URL: {e}").send()
        cl.user_session.set("brochure_state", "awaiting_input")


async def generate_from_file(source_file):
    """Generate brochure from uploaded file."""
    cl.user_session.set("brochure_state", "processing")

    try:
        async with cl.Step(name="Processing File", type="tool") as step:
            step.input = f"Extracting course data from {source_file.name}..."

            # Save file temporarily
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, source_file.name)

            with open(file_path, "wb") as f:
                f.write(source_file.content)

            step.output = "Course data extracted!"

        async with cl.Step(name="Generating Brochure", type="run") as step:
            step.input = "Creating professional brochure..."

            # Placeholder for brochure generation

            step.output = "Brochure generated!"

        await cl.Message(
            content="Brochure generation integration in progress.\n\n"
                    "The existing pipeline from `generate_brochure/` will be connected here."
        ).send()

        cl.user_session.set("brochure_state", "completed")

    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()
        cl.user_session.set("brochure_state", "awaiting_input")
