"""
Courseware Module - Chainlit

Handles courseware document generation:
- Assessment Plan (AP)
- Facilitator Guide (FG)
- Learner Guide (LG)
- Lesson Plan (LP)

Author: Courseware Generator Team
Date: February 2026
"""

import sys
import os
import asyncio
import tempfile
import zipfile
import io

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl


async def on_start():
    """Called when Courseware profile is selected."""
    cl.user_session.set("cw_state", "awaiting_file")
    cl.user_session.set("cp_file", None)
    cl.user_session.set("selected_docs", {"lg": True, "ap": True, "lp": True, "fg": True})


async def on_message(message: cl.Message):
    """Handle messages in Courseware context."""
    state = cl.user_session.get("cw_state", "awaiting_file")
    content = message.content.lower()

    if state == "awaiting_file":
        if any(kw in content for kw in ["upload", "start", "begin", "generate"]):
            await request_file_upload()
        elif "all" in content:
            cl.user_session.set("selected_docs", {"lg": True, "ap": True, "lp": True, "fg": True})
            await request_file_upload()
        else:
            # Check for specific document requests
            selected = {"lg": False, "ap": False, "lp": False, "fg": False}
            if any(kw in content for kw in ["learning guide", "lg", "learner"]):
                selected["lg"] = True
            if any(kw in content for kw in ["assessment plan", "ap"]):
                selected["ap"] = True
            if any(kw in content for kw in ["lesson plan", "lp"]):
                selected["lp"] = True
            if any(kw in content for kw in ["facilitator", "fg"]):
                selected["fg"] = True

            if any(selected.values()):
                cl.user_session.set("selected_docs", selected)
                docs = [k.upper() for k, v in selected.items() if v]
                await cl.Message(content=f"I'll generate: {', '.join(docs)}. Upload your Course Proposal.").send()
                await request_file_upload()
            else:
                await cl.Message(
                    content="Upload your Course Proposal to generate courseware documents."
                ).send()

    elif state == "awaiting_selection":
        await on_message_selection(content)

    elif state == "processing":
        await cl.Message(content="Processing is in progress. Please wait...").send()

    elif state == "completed":
        if any(kw in content for kw in ["another", "new", "again"]):
            await on_start()
            await cl.Message(content="Ready to generate new courseware. Upload your Course Proposal.").send()
        else:
            await cl.Message(content="Your documents are ready above. Say 'new' to create more.").send()


async def on_message_selection(content: str):
    """Handle document selection message."""
    selected = cl.user_session.get("selected_docs", {})

    if "all" in content:
        selected = {"lg": True, "ap": True, "lp": True, "fg": True}
    else:
        if "lg" in content or "learning" in content or "learner" in content:
            selected["lg"] = True
        if "ap" in content or "assessment" in content:
            selected["ap"] = True
        if "lp" in content or "lesson" in content:
            selected["lp"] = True
        if "fg" in content or "facilitator" in content:
            selected["fg"] = True

    cl.user_session.set("selected_docs", selected)

    if any(selected.values()):
        await on_generate_all()
    else:
        await cl.Message(content="Please specify which documents to generate (LG, AP, LP, FG) or say 'all'.").send()


async def on_file_upload(files: list):
    """Handle file uploads."""
    if not files:
        return

    # Accept DOCX or XLSX
    valid_files = [f for f in files if f.name.endswith(('.docx', '.xlsx'))]

    if not valid_files:
        await cl.Message(content="Please upload a Course Proposal (.docx or .xlsx).").send()
        return

    cp_file = valid_files[0]
    cl.user_session.set("cp_file", cp_file)

    await cl.Message(content=f"Received: **{cp_file.name}**").send()

    # Ask for document selection
    actions = [
        cl.Action(name="courseware_generate_all", value="all", label="Generate All (AP, FG, LG, LP)"),
        cl.Action(name="courseware_select_docs", value="select", label="Select Documents"),
    ]

    await cl.Message(
        content="Which documents would you like to generate?",
        actions=actions
    ).send()

    cl.user_session.set("cw_state", "awaiting_selection")


async def request_file_upload():
    """Request file upload from user."""
    files = await cl.AskFileMessage(
        content="Please upload your Course Proposal (.docx or .xlsx):",
        accept=[
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ],
        max_files=1,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def on_generate_all():
    """Generate all selected documents."""
    cl.user_session.set("selected_docs", {"lg": True, "ap": True, "lp": True, "fg": True})
    await process_courseware()


async def on_select_documents():
    """Show document selection."""
    await cl.Message(
        content="Tell me which documents you want:\n"
                "- **LG** - Learning Guide\n"
                "- **AP** - Assessment Plan\n"
                "- **LP** - Lesson Plan\n"
                "- **FG** - Facilitator Guide\n\n"
                "Or say 'all' for everything."
    ).send()


async def process_courseware():
    """Process and generate courseware documents."""
    cp_file = cl.user_session.get("cp_file")
    selected_docs = cl.user_session.get("selected_docs", {})

    if not cp_file:
        await cl.Message(content="No Course Proposal found. Please upload one first.").send()
        cl.user_session.set("cw_state", "awaiting_file")
        return

    cl.user_session.set("cw_state", "processing")

    docs_to_generate = [k.upper() for k, v in selected_docs.items() if v]
    await cl.Message(content=f"Generating: {', '.join(docs_to_generate)}...").send()

    try:
        async with cl.Step(name="Generating Courseware", type="run") as step:
            step.input = f"Processing {cp_file.name}..."

            # Save uploaded file
            temp_dir = tempfile.mkdtemp()
            input_path = os.path.join(temp_dir, cp_file.name)

            with open(input_path, "wb") as f:
                f.write(cp_file.content)

            output_files = []

            # Generate each selected document
            # Note: Actual generation would call existing pipeline functions
            # This is a placeholder for the integration

            step.output = "Generation complete!"

            # For now, show a message about the integration
            await cl.Message(
                content="Courseware generation integration in progress.\n\n"
                        "The existing pipeline from `generate_ap_fg_lg_lp/` will be connected here."
            ).send()

        cl.user_session.set("cw_state", "completed")

    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()
        cl.user_session.set("cw_state", "awaiting_file")
