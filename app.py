"""
WSQ Courseware Generator - Chainlit Application

Main entry point for the Chainlit-based courseware generation assistant.
This replaces the Streamlit app.py with a conversation-first interface.

Author: Courseware Generator Team
Date: February 2026
"""

import sys
import os

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl
from chainlit.input_widget import TextInput, Select, Switch

# Import existing modules (reused from Streamlit app)
from settings.api_manager import load_api_keys, save_api_keys, get_all_available_models
from settings.api_database import (
    get_all_models,
    get_task_model_assignment,
    verify_admin_password,
)
from company.company_manager import get_selected_company, get_organizations
from skills import match_skill_by_keywords, get_skill_action, get_workflow_steps

# Import Chainlit modules
from chainlit_modules import (
    course_proposal,
    courseware,
    assessment,
    slides,
    brochure,
    annex_assessment,
    check_documents,
    settings,
)


# =============================================================================
# Authentication
# =============================================================================

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    Authenticate users against the admin credentials database.
    Returns a User object if authentication succeeds.
    """
    try:
        if verify_admin_password(username, password):
            return cl.User(
                identifier=username,
                metadata={"role": "admin", "provider": "credentials"}
            )
    except Exception as e:
        print(f"Auth error: {e}")
    return None


# =============================================================================
# Chat Profiles
# =============================================================================

@cl.set_chat_profiles
async def chat_profiles():
    """
    Define chat profiles for each module.
    Each profile represents a different workflow/page from the original Streamlit app.
    """
    return [
        cl.ChatProfile(
            name="Course Proposal",
            markdown_description="Generate Course Proposals from TSC documents. Upload a TSC DOCX file to create CP in Excel or Word format.",
            icon="https://api.iconify.design/mdi:file-document-edit.svg",
            starters=[
                cl.Starter(
                    label="Upload TSC Document",
                    message="I want to create a course proposal",
                    icon="https://api.iconify.design/mdi:upload.svg",
                ),
                cl.Starter(
                    label="Excel Format (New CP)",
                    message="Generate course proposal in Excel format",
                    icon="https://api.iconify.design/mdi:file-excel.svg",
                ),
                cl.Starter(
                    label="Word Format (Old CP)",
                    message="Generate course proposal in Word format",
                    icon="https://api.iconify.design/mdi:file-word.svg",
                ),
            ],
        ),
        cl.ChatProfile(
            name="Courseware",
            markdown_description="Generate courseware documents: Assessment Plan (AP), Facilitator Guide (FG), Learner Guide (LG), and Lesson Plan (LP).",
            icon="https://api.iconify.design/mdi:book-open-page-variant.svg",
            starters=[
                cl.Starter(
                    label="Generate All Documents",
                    message="Generate all courseware documents (AP, FG, LG, LP)",
                    icon="https://api.iconify.design/mdi:file-multiple.svg",
                ),
                cl.Starter(
                    label="Learning Guide Only",
                    message="Generate Learning Guide",
                    icon="https://api.iconify.design/mdi:book-education.svg",
                ),
                cl.Starter(
                    label="Facilitator Guide Only",
                    message="Generate Facilitator Guide",
                    icon="https://api.iconify.design/mdi:teach.svg",
                ),
            ],
        ),
        cl.ChatProfile(
            name="Assessment",
            markdown_description="Generate assessment materials: SAQ, Case Study, Practical Performance, Project, Assignment, and more.",
            icon="https://api.iconify.design/mdi:clipboard-check.svg",
            starters=[
                cl.Starter(
                    label="Auto-Detect & Generate",
                    message="Analyze my Facilitator Guide and generate assessments",
                    icon="https://api.iconify.design/mdi:auto-fix.svg",
                ),
                cl.Starter(
                    label="Short Answer Questions",
                    message="Generate Short Answer Questions (SAQ)",
                    icon="https://api.iconify.design/mdi:format-list-numbered.svg",
                ),
                cl.Starter(
                    label="Case Study",
                    message="Generate Case Study assessment",
                    icon="https://api.iconify.design/mdi:briefcase.svg",
                ),
            ],
        ),
        cl.ChatProfile(
            name="Slides",
            markdown_description="Generate presentation slides from course materials using NotebookLM.",
            icon="https://api.iconify.design/mdi:presentation.svg",
            starters=[
                cl.Starter(
                    label="Upload Course Material",
                    message="I want to create presentation slides",
                    icon="https://api.iconify.design/mdi:upload.svg",
                ),
                cl.Starter(
                    label="From Facilitator Guide",
                    message="Generate slides from Facilitator Guide",
                    icon="https://api.iconify.design/mdi:file-presentation-box.svg",
                ),
            ],
        ),
        cl.ChatProfile(
            name="Brochure",
            markdown_description="Generate professional course brochures from course data or web URLs.",
            icon="https://api.iconify.design/mdi:newspaper-variant.svg",
            starters=[
                cl.Starter(
                    label="From Course Proposal",
                    message="Create brochure from my course proposal",
                    icon="https://api.iconify.design/mdi:file-document.svg",
                ),
                cl.Starter(
                    label="From URL",
                    message="Create brochure from a course URL",
                    icon="https://api.iconify.design/mdi:link.svg",
                ),
            ],
        ),
        cl.ChatProfile(
            name="Add to AP",
            markdown_description="Merge assessment documents into Assessment Plan as annexes.",
            icon="https://api.iconify.design/mdi:file-link.svg",
            starters=[
                cl.Starter(
                    label="Upload Documents",
                    message="I want to add assessments to my Assessment Plan",
                    icon="https://api.iconify.design/mdi:upload-multiple.svg",
                ),
            ],
        ),
        cl.ChatProfile(
            name="Check Documents",
            markdown_description="Verify supporting documents: extract entities, match against training records, verify UEN.",
            icon="https://api.iconify.design/mdi:file-search.svg",
            starters=[
                cl.Starter(
                    label="Upload Documents",
                    message="I want to verify my supporting documents",
                    icon="https://api.iconify.design/mdi:upload.svg",
                ),
                cl.Starter(
                    label="Verify UEN",
                    message="Verify a company UEN",
                    icon="https://api.iconify.design/mdi:domain.svg",
                ),
            ],
        ),
        cl.ChatProfile(
            name="Settings",
            markdown_description="Configure API keys, LLM models, and application preferences.",
            icon="https://api.iconify.design/mdi:cog.svg",
            starters=[
                cl.Starter(
                    label="API Keys",
                    message="Configure API keys",
                    icon="https://api.iconify.design/mdi:key.svg",
                ),
                cl.Starter(
                    label="Model Selection",
                    message="Change default model",
                    icon="https://api.iconify.design/mdi:brain.svg",
                ),
                cl.Starter(
                    label="View Current Settings",
                    message="Show my current settings",
                    icon="https://api.iconify.design/mdi:information.svg",
                ),
            ],
        ),
    ]


# =============================================================================
# Chat Start Handler
# =============================================================================

@cl.on_chat_start
async def on_chat_start():
    """
    Initialize the chat session based on the selected profile.
    Each profile triggers a different workflow.
    """
    # Get the selected chat profile
    chat_profile = cl.user_session.get("chat_profile")
    user = cl.user_session.get("user")

    # Store user preferences
    cl.user_session.set("initialized", True)

    # Initialize company selection (default to first)
    organizations = get_organizations()
    if organizations:
        cl.user_session.set("selected_company", organizations[0])
    else:
        cl.user_session.set("selected_company", {"name": "Default", "uen": ""})

    # Initialize model selection
    api_keys = load_api_keys()
    cl.user_session.set("api_keys", api_keys)

    # Welcome message based on profile
    welcome_messages = {
        "Course Proposal": (
            "Welcome to **Course Proposal Generator**!\n\n"
            "I'll help you create a Course Proposal from your TSC document.\n\n"
            "**To get started:**\n"
            "1. Upload your TSC document (.docx)\n"
            "2. Choose output format (Excel or Word)\n"
            "3. I'll generate your Course Proposal\n\n"
            "Ready? Upload your TSC document to begin!"
        ),
        "Courseware": (
            "Welcome to **Courseware Generator**!\n\n"
            "I can generate these documents from your Course Proposal:\n"
            "- **Assessment Plan (AP)**\n"
            "- **Facilitator Guide (FG)**\n"
            "- **Learner Guide (LG)**\n"
            "- **Lesson Plan (LP)**\n\n"
            "Upload your approved Course Proposal to get started!"
        ),
        "Assessment": (
            "Welcome to **Assessment Generator**!\n\n"
            "I support **9 assessment types**:\n"
            "- SAQ (Short Answer Questions)\n"
            "- Case Study\n"
            "- Practical Performance\n"
            "- Project\n"
            "- Assignment\n"
            "- Oral Interview\n"
            "- Demonstration\n"
            "- Role Play\n"
            "- Oral Questioning\n\n"
            "Upload your Facilitator Guide and I'll auto-detect which assessments to generate!"
        ),
        "Slides": (
            "Welcome to **Slides Generator**!\n\n"
            "I'll create presentation slides from your course materials using NotebookLM.\n\n"
            "**Supported inputs:**\n"
            "- Facilitator Guide (.docx)\n"
            "- Learner Guide (.docx)\n"
            "- Course Proposal (.docx)\n"
            "- PDF documents\n\n"
            "Upload your course material to begin!"
        ),
        "Brochure": (
            "Welcome to **Brochure Generator**!\n\n"
            "I'll create a professional course brochure for marketing.\n\n"
            "**Options:**\n"
            "1. Generate from Course Proposal data\n"
            "2. Scrape course info from a URL\n\n"
            "How would you like to create your brochure?"
        ),
        "Add to AP": (
            "Welcome to **Assessment Plan Merger**!\n\n"
            "I'll help you add assessment documents as annexes to your Assessment Plan.\n\n"
            "**You'll need:**\n"
            "1. Your Assessment Plan (.docx)\n"
            "2. Assessment question and answer papers\n\n"
            "Ready? Upload your Assessment Plan first!"
        ),
        "Check Documents": (
            "Welcome to **Document Verification**!\n\n"
            "I can help you verify supporting documents:\n"
            "- **Extract entities** (names, companies, UEN)\n"
            "- **Match against training records**\n"
            "- **Verify UEN with ACRA**\n\n"
            "Upload documents (PDF or images) to start verification!"
        ),
        "Settings": (
            "Welcome to **Settings**!\n\n"
            "Here you can configure:\n"
            "- **API Keys** (OpenRouter, OpenAI, Anthropic, etc.)\n"
            "- **Default Model** for each task\n"
            "- **Company Selection**\n\n"
            "What would you like to configure?"
        ),
    }

    welcome = welcome_messages.get(
        chat_profile,
        "Welcome to **WSQ Courseware Generator**!\n\nSelect a profile from the dropdown to get started."
    )

    await cl.Message(content=welcome).send()

    # Trigger profile-specific initialization
    if chat_profile == "Course Proposal":
        await course_proposal.on_start()
    elif chat_profile == "Courseware":
        await courseware.on_start()
    elif chat_profile == "Assessment":
        await assessment.on_start()
    elif chat_profile == "Slides":
        await slides.on_start()
    elif chat_profile == "Brochure":
        await brochure.on_start()
    elif chat_profile == "Add to AP":
        await annex_assessment.on_start()
    elif chat_profile == "Check Documents":
        await check_documents.on_start()
    elif chat_profile == "Settings":
        await settings.on_start()


# =============================================================================
# Message Handler
# =============================================================================

@cl.on_message
async def on_message(message: cl.Message):
    """
    Handle incoming messages based on the current chat profile.
    Also supports natural language skill matching and file uploads.
    """
    chat_profile = cl.user_session.get("chat_profile")
    content = message.content.strip()

    # Check for file attachments (spontaneous upload)
    if message.elements:
        file_elements = [e for e in message.elements if hasattr(e, 'path')]
        if file_elements:
            await handle_file_upload(file_elements)
            return

    # Check for skill command (e.g., /generate_brochure)
    skill_action = get_skill_action(content)
    if skill_action:
        response = skill_action.get("response", "")
        navigate = skill_action.get("navigate", "")

        await cl.Message(content=response).send()

        if navigate:
            await cl.Message(
                content=f"**Tip:** Switch to the **{navigate}** profile to continue with this task."
            ).send()
        return

    # Check for natural language skill match
    skill_match = match_skill_by_keywords(content)
    if skill_match:
        response = skill_match.get("response", "")
        navigate = skill_match.get("navigate", "")

        await cl.Message(content=response).send()

        if navigate:
            await cl.Message(
                content=f"**Tip:** Switch to the **{navigate}** profile to continue."
            ).send()
        return

    # Check for workflow request
    lower_content = content.lower()
    if any(kw in lower_content for kw in ["workflow", "process", "steps", "what order"]):
        workflow = get_workflow_steps()
        await cl.Message(content=workflow).send()
        return

    # Check for help request
    if any(kw in lower_content for kw in ["help", "what can you do", "menu", "options"]):
        help_text = (
            "I can help you with:\n\n"
            "- **Course Proposal** - Generate CP from TSC documents\n"
            "- **Courseware** - Generate AP, FG, LG, LP\n"
            "- **Assessment** - Create 9 types of assessments\n"
            "- **Slides** - Generate presentations via NotebookLM\n"
            "- **Brochure** - Create marketing brochures\n"
            "- **Add to AP** - Merge assessments into AP\n"
            "- **Check Documents** - Verify supporting docs\n"
            "- **Settings** - Configure API keys and models\n\n"
            "Select a profile from the dropdown above, or tell me what you'd like to do!"
        )
        await cl.Message(content=help_text).send()
        return

    # Route to profile-specific handler
    handlers = {
        "Course Proposal": course_proposal.on_message,
        "Courseware": courseware.on_message,
        "Assessment": assessment.on_message,
        "Slides": slides.on_message,
        "Brochure": brochure.on_message,
        "Add to AP": annex_assessment.on_message,
        "Check Documents": check_documents.on_message,
        "Settings": settings.on_message,
    }

    handler = handlers.get(chat_profile)
    if handler:
        await handler(message)
    else:
        await cl.Message(
            content="Please select a profile from the dropdown to get started."
        ).send()


# =============================================================================
# Settings Update Handler
# =============================================================================

@cl.on_settings_update
async def on_settings_update(settings_update):
    """
    Handle settings updates from ChatSettings forms.
    """
    await settings.on_settings_update(settings_update)


# =============================================================================
# Action Callbacks
# =============================================================================

# Course Proposal Actions
@cl.action_callback("cp_excel_format")
async def on_cp_excel_format(action):
    await course_proposal.on_format_selected("excel")


@cl.action_callback("cp_docx_format")
async def on_cp_docx_format(action):
    await course_proposal.on_format_selected("docx")


# Assessment Actions
@cl.action_callback("assessment_generate_all")
async def on_assessment_generate_all(action):
    await assessment.on_generate_all()


@cl.action_callback("assessment_customize")
async def on_assessment_customize(action):
    await assessment.on_customize()


# Courseware Actions
@cl.action_callback("courseware_generate_all")
async def on_courseware_generate_all(action):
    await courseware.on_generate_all()


@cl.action_callback("courseware_select_docs")
async def on_courseware_select_docs(action):
    await courseware.on_select_documents()


# Settings Actions
@cl.action_callback("settings_api_keys")
async def on_settings_api_keys(action):
    await settings.show_api_keys()


@cl.action_callback("settings_models")
async def on_settings_models(action):
    await settings.show_models()


@cl.action_callback("settings_company")
async def on_settings_company(action):
    await settings.show_company_selection()


# =============================================================================
# File Upload Helper
# =============================================================================

async def handle_file_upload(files: list):
    """
    Handle file uploads (from message elements).
    Route to appropriate handler based on chat profile.
    """
    chat_profile = cl.user_session.get("chat_profile")

    if chat_profile == "Course Proposal":
        await course_proposal.on_file_upload(files)
    elif chat_profile == "Courseware":
        await courseware.on_file_upload(files)
    elif chat_profile == "Assessment":
        await assessment.on_file_upload(files)
    elif chat_profile == "Slides":
        await slides.on_file_upload(files)
    elif chat_profile == "Add to AP":
        await annex_assessment.on_file_upload(files)
    elif chat_profile == "Check Documents":
        await check_documents.on_file_upload(files)
    else:
        await cl.Message(
            content=f"Received {len(files)} file(s). Please select a profile to process them."
        ).send()


# =============================================================================
# Session Resume Handler
# =============================================================================

@cl.on_chat_resume
async def on_chat_resume(thread):
    """
    Handle resuming a previous chat session.
    Restore session state from the thread.
    """
    chat_profile = cl.user_session.get("chat_profile")

    await cl.Message(
        content=f"Welcome back! You're continuing in the **{chat_profile}** profile.\n\n"
                "Your previous session has been restored. How can I help you?"
    ).send()
