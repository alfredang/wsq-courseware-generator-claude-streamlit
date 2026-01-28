# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization
import asyncio
import os

# Import skills loader
from skills import get_skill_response, get_skill_action, get_skills_system_message, list_skill_commands

# Lazy loading functions for better performance
def lazy_import_assessment():
    import generate_assessment.assessment_generation as assessment_generation
    return assessment_generation

def lazy_import_courseware():
    import generate_ap_fg_lg_lp.courseware_generation as courseware_generation
    return courseware_generation

def lazy_import_brochure_v2():
    import generate_brochure.brochure_generation as brochure_generation
    return brochure_generation

def lazy_import_annex_v2():
    import add_assessment_to_ap.annex_assessment_v2 as annex_assessment_v2
    return annex_assessment_v2

def lazy_import_course_proposal():
    import generate_cp.app as course_proposal_app
    return course_proposal_app

def lazy_import_docs():
    import check_documents.sup_doc as sup_doc
    return sup_doc

def lazy_import_settings():
    import settings.settings as settings
    return settings

def lazy_import_company_settings():
    import company.company_settings as company_settings
    return company_settings

def lazy_import_slides():
    import generate_slides.slides_generation as slides_generation
    return slides_generation


def display_homepage():
    """Display homepage with navigation boxes and chatbot"""
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
            }
            .card-header {
                text-align: center;
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 0.25rem;
            }
            .card-desc {
                text-align: center;
                font-size: 0.8rem;
                color: #888;
                margin-bottom: 0.5rem;
            }
        </style>
        """, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-size: 1.75rem;'>WSQ Courseware Assistant with OpenAI Multi Agents</h2>", unsafe_allow_html=True)

    # Navigation boxes - 2 columns, 3 rows
    modules = [
        {"name": "Generate CP", "icon": "📄", "desc": "Create Course Proposals", "menu": "Generate CP"},
        {"name": "Generate AP/FG/LG/LP", "icon": "📚", "desc": "Generate Courseware Documents", "menu": "Generate AP/FG/LG/LP"},
        {"name": "Generate Assessment", "icon": "✅", "desc": "Create Assessment Materials", "menu": "Generate Assessment"},
        {"name": "Generate Slides", "icon": "🎯", "desc": "Create Presentation Slides", "menu": "Generate Slides"},
        {"name": "Generate Brochure", "icon": "📰", "desc": "Design Course Brochures", "menu": "Generate Brochure"},
        {"name": "Add Assessment to AP", "icon": "📎", "desc": "Attach Assessments to AP", "menu": "Add Assessment to AP"},
        {"name": "Check Documents", "icon": "🔍", "desc": "Validate Supporting Documents", "menu": "Check Documents"},
    ]

    # Display modules in 2 columns, 3 rows
    for i in range(0, len(modules), 2):
        col1, col2 = st.columns(2)

        with col1:
            m = modules[i]
            with st.container(border=True):
                st.markdown(f"<div class='card-header'>{m['icon']} {m['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-desc'>{m['desc']}</div>", unsafe_allow_html=True)
                if st.button("Open", key=f"nav_{i}", use_container_width=True):
                    st.session_state['nav_to'] = m['menu']
                    st.rerun()

        with col2:
            if i + 1 < len(modules):
                m = modules[i + 1]
                with st.container(border=True):
                    st.markdown(f"<div class='card-header'>{m['icon']} {m['name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-desc'>{m['desc']}</div>", unsafe_allow_html=True)
                    if st.button("Open", key=f"nav_{i+1}", use_container_width=True):
                        st.session_state['nav_to'] = m['menu']
                        st.rerun()



def get_chatbot_system_message():
    """Generate the chatbot system message with dynamically loaded skills."""
    base_message = """You are an AI assistant for WSQ (Workforce Skills Qualifications) courseware generation. You help users create training materials for Singapore's national credential system.

**IMPORTANT**: You are a skill-driven assistant. When users ask questions, ALWAYS check if their request relates to one of your skills. Use the skill's detailed instructions and knowledge to provide accurate, specific guidance.

"""
    # Add skills from .skills folder
    skills_message = get_skills_system_message()

    response_guide = """
## How to Respond

1. **Identify the relevant skill** - Match user requests to your skills, even without exact commands
2. **Use skill knowledge** - Reference the Instructions section of relevant skills for detailed guidance
3. **Provide specific answers** - Use the process steps, tips, and requirements from skills
4. **Offer to navigate** - Tell users you can take them to the relevant module
5. **Be concise but thorough** - Users are busy training professionals

## Navigation

Users can access modules from the sidebar, or type skill commands:
- `/generate_course_proposal` - Create Course Proposals
- `/generate_ap_fg_lg_lp` - Generate courseware documents
- `/generate_assessment` - Create assessment materials
"""
    return base_message + skills_message + response_guide


def handle_chat_logic(prompt):
    """Process chat message and get response from AI"""
    if not prompt or not prompt.strip():
        return

    # Check for skill commands using the skills loader
    skill_action = get_skill_action(prompt.strip())
    if skill_action:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.chat_messages.append({"role": "assistant", "content": skill_action['response']})
        # Auto-navigate if skill has a navigate target
        if skill_action.get('navigate'):
            st.session_state['nav_to'] = skill_action['navigate']
        st.rerun()
        return

    # Add user message to history
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    try:
        from settings.api_manager import load_api_keys
        from settings.api_database import get_task_model_assignment, get_model_by_name

        api_keys = load_api_keys()

        # Check for specific Chatbot assignment first
        chatbot_assignment = get_task_model_assignment("chatbot")

        if chatbot_assignment:
            chat_model = chatbot_assignment.get("model_name")
            api_provider = chatbot_assignment.get("api_provider", "OPENROUTER")
        else:
            # Fallback to selected model (which handles page-specific or global defaults)
            chat_model = st.session_state.get('selected_model')
            api_provider = st.session_state.get('selected_api_provider', 'OPENROUTER')

        api_key = api_keys.get(f"{api_provider}_API_KEY", "")

        if not chat_model:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": "No model selected. Please select a model from the sidebar."
            })
        elif api_key:
            # Get the model ID from database
            model_info = get_model_by_name(chat_model)
            # model_id is in config.model, not at top level
            if model_info and model_info.get("config"):
                model_id = model_info["config"].get("model", chat_model)
            else:
                model_id = chat_model

            # Build messages list for chat
            messages = []
            for msg in st.session_state.chat_messages:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Use appropriate SDK based on provider
            with st.spinner("Thinking..."):
                if api_provider == "ANTHROPIC":
                    # Use Anthropic's native SDK
                    assistant_message = _call_anthropic_chat(api_key, model_id, messages)
                elif api_provider == "GEMINI":
                    # Use Google's native Generative AI SDK
                    assistant_message = _call_gemini_chat(api_key, model_id, messages)
                else:
                    # Use OpenAI-compatible SDK for other providers (OpenRouter, OpenAI, Groq, Grok, DeepSeek)
                    assistant_message = _call_openai_compatible_chat(api_key, api_provider, model_id, messages)

            st.session_state.chat_messages.append({"role": "assistant", "content": assistant_message})
        else:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"{api_provider}_API_KEY not configured. Please set up your API key in Settings > API & Models to use the chat feature."
            })
    except Exception as e:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": f"Error: {str(e)}"
        })
    st.rerun()


def _call_anthropic_chat(api_key: str, model_id: str, messages: list) -> str:
    """Call Anthropic's native API for chat"""
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Anthropic expects system message separately
        system_message = get_chatbot_system_message()

        # Convert messages format (Anthropic doesn't use 'system' role in messages)
        anthropic_messages = []
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = client.messages.create(
            model=model_id,
            max_tokens=4096,
            system=system_message,
            messages=anthropic_messages
        )

        return response.content[0].text
    except Exception as e:
        raise Exception(f"Anthropic API error: {str(e)}")


def _call_gemini_chat(api_key: str, model_id: str, messages: list) -> str:
    """Call Google's Gemini API for chat"""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        # Create the model - handle model_id format (might have 'google/' prefix)
        if model_id.startswith("google/"):
            model_id = model_id.replace("google/", "")

        model = genai.GenerativeModel(
            model_name=model_id,
            system_instruction=get_chatbot_system_message()
        )

        # Convert messages to Gemini format
        gemini_history = []
        current_message = None

        for msg in messages[:-1]:  # All messages except the last one go into history
            if msg["role"] == "user":
                gemini_history.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_history.append({"role": "model", "parts": [msg["content"]]})

        # Get the last user message
        if messages and messages[-1]["role"] == "user":
            current_message = messages[-1]["content"]
        else:
            current_message = messages[-1]["content"] if messages else ""

        # Start chat with history
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(current_message)

        return response.text
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


def _call_openai_compatible_chat(api_key: str, api_provider: str, model_id: str, messages: list) -> str:
    """Call OpenAI-compatible API for chat (OpenRouter, OpenAI, Groq, Grok, DeepSeek)"""
    try:
        from openai import OpenAI

        # Provider base URLs (all OpenAI-compatible)
        base_urls = {
            "OPENROUTER": "https://openrouter.ai/api/v1",
            "OPENAI": "https://api.openai.com/v1",
            "GROQ": "https://api.groq.com/openai/v1",
            "GROK": "https://api.x.ai/v1",
            "DEEPSEEK": "https://api.deepseek.com/v1",
        }

        base_url = base_urls.get(api_provider, "https://openrouter.ai/api/v1")

        client = OpenAI(api_key=api_key, base_url=base_url)

        # Add system message if not present
        chat_messages = [{"role": "system", "content": get_chatbot_system_message()}]
        chat_messages.extend(messages)

        response = client.chat.completions.create(
            model=model_id,
            messages=chat_messages,
            max_tokens=4096
        )

        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"{api_provider} API error: {str(e)}")

def display_bottom_chatbot():
    """Display a permanent chatbot at the bottom of the page"""
    # Initialize session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Collapsible expander for chatbot
    with st.expander("💬 AI Assistant - Ask me anything about WSQ courseware", expanded=False):
        # Chat messages display (scrollable container)
        messages_container = st.container(height=300)
        with messages_container:
            if not st.session_state.chat_messages:
                # Build welcome message with dynamic skills list
                skill_commands = list_skill_commands()
                skills_list = ", ".join([f"`{cmd}`" for cmd in skill_commands]) if skill_commands else "No skills configured"
                welcome_msg = f"""Hi! I can help you with WSQ courseware. Try these commands: {skills_list}

Or just ask me anything!"""
                st.chat_message("assistant").markdown(welcome_msg)
            for msg in st.session_state.chat_messages:
                st.chat_message(msg["role"]).markdown(msg["content"])

        # Input row with text input and clear button
        col1, col2 = st.columns([6, 1])

        with col1:
            # Input using callback
            def send_message():
                user_input = st.session_state.get("chat_user_input", "")
                if user_input and user_input.strip():
                    handle_chat_logic(user_input)
                    st.session_state.chat_user_input = ""

            st.text_input(
                "Message",
                placeholder="Type your message and press Enter...",
                key="chat_user_input",
                on_change=send_message,
                label_visibility="collapsed"
            )

        with col2:
            if st.button("Clear", key="clear_chat_btn", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()


st.set_page_config(layout="wide")

# Global CSS
st.markdown("""
<style>
    /* Sidebar styling - wider width */
    [data-testid="stSidebar"] { min-width: 350px; max-width: 350px; }
    [data-testid="stSidebar"] > div:first-child { width: 350px; }
    [data-testid="stSidebar"] hr { margin: 0.5rem 0 !important; }

    /* Disabled selectbox styling - keep text white */
    [data-testid="stSidebar"] [data-baseweb="select"] [aria-disabled="true"] {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] [aria-disabled="true"] div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize API system - cached
@st.cache_resource
def initialize_apis():
    try:
        from settings.api_manager import initialize_api_system
        initialize_api_system()
    except ImportError:
        pass

initialize_apis()

# Ensure built-in models are always up to date (runs on each session start)
if 'models_refreshed' not in st.session_state:
    try:
        from settings.api_database import refresh_builtin_models
        refresh_builtin_models()
        st.session_state['models_refreshed'] = True
    except Exception:
        pass

# Get organizations and setup company selection - cached
@st.cache_data
def get_cached_organizations():
    return get_organizations()

@st.cache_data
def get_cached_default_organization():
    return get_default_organization()

organizations = get_cached_organizations()
default_org = get_cached_default_organization()

with st.sidebar:
    # Company Selection
    if organizations:
        company_names = [org["name"] for org in organizations]

        # Find Tertiary Infotech as default company
        default_company_idx = 0
        for i, name in enumerate(company_names):
            if "tertiary infotech" in name.lower():
                default_company_idx = i
                break

        # Use default on first load, then respect user selection
        if 'selected_company_idx' not in st.session_state:
            st.session_state['selected_company_idx'] = default_company_idx

        # Validate stored index to prevent out-of-range errors
        if st.session_state['selected_company_idx'] >= len(organizations):
            st.session_state['selected_company_idx'] = default_company_idx

        selected_company_idx = st.selectbox(
            "Select Company:",
            range(len(company_names)),
            format_func=lambda x: company_names[x],
            index=st.session_state['selected_company_idx']
        )

        # Store selection in session state
        st.session_state['selected_company_idx'] = selected_company_idx
        selected_company = organizations[selected_company_idx]
    else:
        selected_company = default_org
        st.session_state['selected_company_idx'] = 0

    # Store selected company in session state for other modules
    st.session_state['selected_company'] = selected_company

    # Model Selection (no divider for compact layout)
    from settings.api_manager import get_all_available_models, get_all_api_key_configs, load_api_keys
    from settings.api_database import get_all_models as db_get_all_models, get_task_model_assignment

    # Mapping from menu names to task IDs
    MENU_TO_TASK_ID = {
        "Home": "chatbot",
        "Generate CP": "generate_cp",
        "Generate AP/FG/LG/LP": "generate_courseware",
        "Generate Assessment": "generate_assessment",
        "Generate Slides": "generate_slides",
        "Generate Brochure": "generate_brochure",
        "Add Assessment to AP": "add_assessment_ap",
        "Check Documents": "check_documents",
    }

    # Get all API key configurations and current keys
    api_key_configs = get_all_api_key_configs()
    current_keys = load_api_keys()

    # Build API provider options (only show configured ones first, then unconfigured)
    configured_providers = []
    unconfigured_providers = []
    for config in api_key_configs:
        provider_name = config["key_name"].replace("_API_KEY", "")
        display = config['display_name']
        is_configured = bool(current_keys.get(config["key_name"], ""))
        if is_configured:
            configured_providers.append((provider_name, display))
        else:
            unconfigured_providers.append((provider_name, f"{display} (No API Key)"))

    # Combine: configured first, then unconfigured
    all_providers = configured_providers + unconfigured_providers
    provider_names = [p[0] for p in all_providers]
    provider_display = [p[1] for p in all_providers]

    # Check if current menu has a model assignment
    current_menu = st.session_state.get('previous_menu_selection', 'Home')
    task_id = MENU_TO_TASK_ID.get(current_menu, None)
    task_assignment = get_task_model_assignment(task_id) if task_id else None

    # Fallback to Global Default if no specific task assignment
    if not task_assignment:
        task_assignment = get_task_model_assignment("global")

    # If task has an assignment, use it; otherwise use session state or default
    if task_assignment:
        assigned_provider = task_assignment.get("api_provider", "OPENROUTER")
        assigned_model = task_assignment.get("model_name", "")
        # Update session state to reflect the assignment
        st.session_state['selected_api_provider'] = assigned_provider
        st.session_state['assigned_model_for_task'] = assigned_model
    else:
        # Default to OPENROUTER if no assignment and no previous selection
        if 'selected_api_provider' not in st.session_state:
            st.session_state['selected_api_provider'] = "OPENROUTER"
        # Clear any task-specific model assignment
        if 'assigned_model_for_task' in st.session_state:
            del st.session_state['assigned_model_for_task']

    # Find index of current provider
    try:
        default_provider_idx = provider_names.index(st.session_state['selected_api_provider'])
    except ValueError:
        default_provider_idx = 0

    # API Provider selector (disabled if task has assignment)
    selected_provider_idx = st.selectbox(
        "API Provider:",
        range(len(provider_names)),
        format_func=lambda x: provider_display[x],
        index=default_provider_idx,
        help="Select which API key to use for models" + (" (Set by Model Assignment)" if task_assignment else ""),
        disabled=bool(task_assignment)
    )
    selected_provider = provider_names[selected_provider_idx]
    if not task_assignment:
        st.session_state['selected_api_provider'] = selected_provider

    # Get all models and filter by selected provider (only show enabled models)
    all_db_models = db_get_all_models(include_builtin=True)
    filtered_models = [m for m in all_db_models
                       if m.get("api_provider", "OPENROUTER") == st.session_state['selected_api_provider']
                       and m.get("is_enabled", True)]

    # If no models for this provider, show message
    if not filtered_models:
        st.warning(f"No models configured for {st.session_state['selected_api_provider']}. Add models in Settings → Add Custom Model.")
        model_names = []
        st.session_state['selected_model'] = None
        st.session_state['selected_model_config'] = None
    else:
        model_names = [m["name"] for m in filtered_models]

        # Determine which model to select
        # If task has an assignment, use assigned model
        if task_assignment and st.session_state.get('assigned_model_for_task') in model_names:
            current_idx = model_names.index(st.session_state['assigned_model_for_task'])
        elif 'user_selected_model' in st.session_state and st.session_state['user_selected_model'] in model_names:
            current_idx = model_names.index(st.session_state['user_selected_model'])
        else:
            current_idx = 0

        # Model selector (disabled if task has assignment)
        selected_model_idx = st.selectbox(
            "Select Model:",
            range(len(model_names)),
            format_func=lambda x: model_names[x],
            index=current_idx,
            disabled=bool(task_assignment)
        )

        # Track user's explicit model selection (only if no task assignment)
        if not task_assignment and model_names[selected_model_idx] != model_names[current_idx]:
            st.session_state['user_selected_model'] = model_names[selected_model_idx]

        # Store selection in session state
        st.session_state['selected_model'] = model_names[selected_model_idx]

        # Get full model config with API key
        all_models = get_all_available_models()
        if model_names[selected_model_idx] in all_models:
            st.session_state['selected_model_config'] = all_models[model_names[selected_model_idx]]
        else:
            st.session_state['selected_model_config'] = None

    # Show indicator if using model assignment
    if task_assignment:
        st.caption(f"📌 Using assigned model for {current_menu}")

    # Main features menu (no divider for compact layout)
    menu_options = [
        "Home",
        "Generate CP",
        "Generate AP/FG/LG/LP",
        "Generate Assessment",
        "Generate Slides",
        "Generate Brochure",
        "Add Assessment to AP",
        "Check Documents",
    ]

    menu_icons = [
        "house",
        "filetype-doc",
        "file-earmark-richtext",
        "clipboard-check",
        "easel",
        "file-earmark-pdf",
        "folder-symlink",
        "search",
    ]

    # Handle navigation from homepage boxes
    nav_to = st.session_state.get('nav_to', None)
    if nav_to and nav_to in menu_options:
        st.session_state['current_page'] = nav_to
        st.session_state['nav_to'] = None  # Clear after use

    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Home"

    # Get the default index based on current page
    current_page = st.session_state['current_page']
    if current_page in menu_options:
        default_idx = menu_options.index(current_page)
    else:
        default_idx = 0

    selected = option_menu(
        "",  # Title of the sidebar
        menu_options,
        icons=menu_icons,
        menu_icon="boxes",  # Icon for the sidebar title
        default_index=default_idx,  # Default selected item
    )

    # Update current page when menu selection changes
    if selected != current_page:
        st.session_state['current_page'] = selected

    # Separate Settings section using buttons (compact)
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; font-weight: 600; margin-bottom: 0.3rem;'>Settings</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("API & Models", use_container_width=True):
            st.session_state['settings_page'] = "API & LLM Models"
    with col2:
        if st.button("Companies", use_container_width=True):
            st.session_state['settings_page'] = "Company Management"

    # Powered by footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #888; font-size: 0.8rem;'>
            Powered by <b>Tertiary Infotech Academy Pte Ltd</b>
        </div>
    """, unsafe_allow_html=True)

# Check if a settings page is selected (takes priority)
settings_page = st.session_state.get('settings_page', None)

# Track if user clicked on main menu (not just a rerun)
previous_menu = st.session_state.get('previous_menu_selection', None)
menu_changed = previous_menu is not None and previous_menu != selected
st.session_state['previous_menu_selection'] = selected

# If menu changed, rerun once to update sidebar assignments immediately
if menu_changed:
    st.rerun()

# Main content area (full width)
# Display the selected app - using lazy loading for performance
if settings_page == "API & LLM Models":
    settings = lazy_import_settings()
    settings.llm_settings_app()
    # Only clear settings page when main menu is explicitly clicked
    if menu_changed:
        st.session_state['settings_page'] = None
        st.rerun()

elif settings_page == "Company Management":
    company_settings = lazy_import_company_settings()
    company_settings.company_management_app()
    # Only clear settings page when main menu is explicitly clicked
    if menu_changed:
        st.session_state['settings_page'] = None
        st.rerun()

elif selected == "Home":
    st.session_state['settings_page'] = None
    display_homepage()

elif selected == "Generate CP":
    st.session_state['settings_page'] = None
    course_proposal_app = lazy_import_course_proposal()
    course_proposal_app.app()

elif selected == "Generate AP/FG/LG/LP":
    st.session_state['settings_page'] = None
    courseware_generation = lazy_import_courseware()
    courseware_generation.app()

elif selected == "Generate Assessment":
    st.session_state['settings_page'] = None
    assessment_generation = lazy_import_assessment()
    assessment_generation.app()

elif selected == "Generate Slides":
    st.session_state['settings_page'] = None
    slides_generation = lazy_import_slides()
    slides_generation.app()

elif selected == "Check Documents":
    st.session_state['settings_page'] = None
    sup_doc = lazy_import_docs()
    sup_doc.app()

elif selected == "Generate Brochure":
    st.session_state['settings_page'] = None
    brochure_generation = lazy_import_brochure_v2()
    brochure_generation.app()

elif selected == "Add Assessment to AP":
    st.session_state['settings_page'] = None
    annex_assessment_v2 = lazy_import_annex_v2()
    annex_assessment_v2.app()

# Permanent chatbot at the bottom
st.divider()
display_bottom_chatbot()

