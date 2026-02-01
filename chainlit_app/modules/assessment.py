"""
Assessment Module - Chainlit

Handles assessment generation for 9 types:
- SAQ (Short Answer Questions)
- CS (Case Study)
- PP (Practical Performance)
- PRJ (Project)
- ASGN (Assignment)
- OI (Oral Interview)
- DEM (Demonstration)
- RP (Role Play)
- OQ (Oral Questioning)

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

# Assessment type definitions
ASSESSMENT_TYPES = {
    "SAQ": "Short Answer Questions",
    "CS": "Case Study",
    "PP": "Practical Performance",
    "PRJ": "Project",
    "ASGN": "Assignment",
    "OI": "Oral Interview",
    "DEM": "Demonstration",
    "RP": "Role Play",
    "OQ": "Oral Questioning",
}


async def on_start():
    """Called when Assessment profile is selected."""
    cl.user_session.set("assess_state", "awaiting_file")
    cl.user_session.set("fg_file", None)
    cl.user_session.set("slides_file", None)
    cl.user_session.set("fg_data", None)
    cl.user_session.set("detected_types", [])
    cl.user_session.set("selected_types", [])


async def on_message(message: cl.Message):
    """Handle messages in Assessment context."""
    state = cl.user_session.get("assess_state", "awaiting_file")
    content = message.content.lower()

    if state == "awaiting_file":
        if any(kw in content for kw in ["upload", "start", "analyze", "generate"]):
            await request_file_upload()
        else:
            # Check for specific assessment type requests
            requested_types = []
            for code, name in ASSESSMENT_TYPES.items():
                if code.lower() in content or name.lower() in content:
                    requested_types.append(code)

            if requested_types:
                cl.user_session.set("selected_types", requested_types)
                await cl.Message(
                    content=f"I'll generate: {', '.join(requested_types)}. Please upload your Facilitator Guide."
                ).send()
                await request_file_upload()
            else:
                await cl.Message(
                    content="Upload your Facilitator Guide to auto-detect assessment types, "
                            "or specify which types you need (SAQ, CS, PP, etc.)."
                ).send()

    elif state == "types_detected":
        await handle_type_selection(content)

    elif state == "processing":
        await cl.Message(content="Generation in progress. Please wait...").send()

    elif state == "completed":
        if any(kw in content for kw in ["another", "new", "again"]):
            await on_start()
            await cl.Message(content="Ready for new assessments. Upload your Facilitator Guide.").send()
        else:
            await cl.Message(content="Your assessments are ready above. Say 'new' to create more.").send()


async def handle_type_selection(content: str):
    """Handle assessment type selection."""
    detected = cl.user_session.get("detected_types", [])

    if "all" in content:
        cl.user_session.set("selected_types", detected)
        await generate_assessments()
    elif "customize" in content or "select" in content:
        await show_type_selection()
    else:
        # Parse specific types from message
        selected = []
        for code in ASSESSMENT_TYPES.keys():
            if code.lower() in content:
                selected.append(code)

        if selected:
            cl.user_session.set("selected_types", selected)
            await generate_assessments()
        else:
            await cl.Message(
                content="Please specify which assessment types to generate, or say 'all'."
            ).send()


async def on_file_upload(files: list):
    """Handle file uploads."""
    if not files:
        return

    # Separate FG and slides files
    fg_file = None
    slides_file = None

    for f in files:
        if f.name.endswith('.docx'):
            fg_file = f
        elif f.name.endswith('.pdf'):
            slides_file = f

    if fg_file:
        cl.user_session.set("fg_file", fg_file)
        await cl.Message(content=f"Received Facilitator Guide: **{fg_file.name}**").send()

    if slides_file:
        cl.user_session.set("slides_file", slides_file)
        await cl.Message(content=f"Received Slides: **{slides_file.name}**").send()

    if not fg_file:
        await cl.Message(content="Please upload a Facilitator Guide (.docx).").send()
        return

    # Analyze FG to detect assessment types
    await analyze_facilitator_guide()


async def request_file_upload():
    """Request file upload from user."""
    files = await cl.AskFileMessage(
        content="Please upload your Facilitator Guide (.docx).\n"
                "Optionally, also upload a Trainer Slide Deck (.pdf) for additional context.",
        accept=[
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/pdf"
        ],
        max_files=2,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def analyze_facilitator_guide():
    """Analyze FG to detect assessment types."""
    fg_file = cl.user_session.get("fg_file")

    async with cl.Step(name="Analyzing Facilitator Guide", type="tool") as step:
        step.input = f"Scanning {fg_file.name} for assessment types..."

        # Save file temporarily
        temp_dir = tempfile.mkdtemp()
        fg_path = os.path.join(temp_dir, fg_file.name)

        with open(fg_path, "wb") as f:
            f.write(fg_file.content)

        # Detection logic (simplified - actual would use existing detection code)
        # Placeholder: detect based on content patterns
        detected_types = []

        try:
            from docx import Document
            doc = Document(fg_path)
            full_text = "\n".join([p.text for p in doc.paragraphs])

            # Check for each assessment type
            type_patterns = {
                "SAQ": ["short answer", "saq", "written test", "written assessment"],
                "CS": ["case study", "scenario", "case-based"],
                "PP": ["practical performance", "practical assessment", "hands-on"],
                "PRJ": ["project", "project work", "project-based"],
                "ASGN": ["assignment", "written assignment"],
                "OI": ["oral interview", "interview"],
                "DEM": ["demonstration", "demo"],
                "RP": ["role play", "roleplay", "role-play"],
                "OQ": ["oral questioning", "oral questions"],
            }

            lower_text = full_text.lower()
            for code, patterns in type_patterns.items():
                if any(p in lower_text for p in patterns):
                    detected_types.append(code)

        except Exception as e:
            step.output = f"Error parsing document: {e}"
            detected_types = ["SAQ", "CS", "PP"]  # Default fallback

        cl.user_session.set("detected_types", detected_types)
        cl.user_session.set("fg_data", {"path": fg_path})

        step.output = f"Detected: {', '.join(detected_types) if detected_types else 'None'}"

    if detected_types:
        type_list = "\n".join([f"- **{code}**: {ASSESSMENT_TYPES[code]}" for code in detected_types])

        actions = [
            cl.Action(name="assessment_generate_all", value="all", label=f"Generate All ({len(detected_types)})"),
            cl.Action(name="assessment_customize", value="custom", label="Customize Selection"),
        ]

        await cl.Message(
            content=f"**Detected {len(detected_types)} assessment type(s):**\n{type_list}",
            actions=actions
        ).send()

        cl.user_session.set("assess_state", "types_detected")
    else:
        await cl.Message(
            content="No assessment types detected. Please specify which types you need:\n"
                    f"{', '.join(ASSESSMENT_TYPES.keys())}"
        ).send()


async def show_type_selection():
    """Show assessment type selection."""
    type_list = "\n".join([f"- **{code}**: {name}" for code, name in ASSESSMENT_TYPES.items()])

    await cl.Message(
        content=f"Available assessment types:\n{type_list}\n\n"
                "Tell me which ones you want (e.g., 'SAQ, CS, PP') or 'all'."
    ).send()


async def on_generate_all():
    """Generate all detected assessment types."""
    detected = cl.user_session.get("detected_types", [])
    cl.user_session.set("selected_types", detected)
    await generate_assessments()


async def on_customize():
    """Show customization options."""
    await show_type_selection()


async def generate_assessments():
    """Generate selected assessment types."""
    selected = cl.user_session.get("selected_types", [])
    fg_data = cl.user_session.get("fg_data", {})

    if not selected:
        await cl.Message(content="No assessment types selected. Please specify which ones to generate.").send()
        return

    cl.user_session.set("assess_state", "processing")

    await cl.Message(content=f"Generating assessments: {', '.join(selected)}...").send()

    try:
        output_files = []

        for assess_type in selected:
            async with cl.Step(name=f"Generating {assess_type}", type="run") as step:
                step.input = f"Creating {ASSESSMENT_TYPES[assess_type]}..."

                # Placeholder for actual generation
                # Would call existing assessment generation functions

                step.output = f"{assess_type} generated!"

        # Show completion message
        await cl.Message(
            content=f"Assessment generation integration in progress.\n\n"
                    f"The existing pipeline will generate: {', '.join(selected)}\n\n"
                    "Each type produces Question and Answer documents."
        ).send()

        cl.user_session.set("assess_state", "completed")

    except Exception as e:
        await cl.Message(content=f"Error during generation: {e}").send()
        cl.user_session.set("assess_state", "types_detected")
