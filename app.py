# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization
import asyncio
import os

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

    # Navigation boxes - 3 columns, 2 rows
    col1, col2, col3 = st.columns(3)

    modules = [
        {"name": "Generate CP", "icon": "📄", "desc": "Create Course Proposals", "key": "nav_cp"},
        {"name": "Generate AP/FG/LG/LP", "icon": "📚", "desc": "Generate Courseware Documents", "key": "nav_courseware"},
        {"name": "Generate Assessment", "icon": "✅", "desc": "Create Assessment Materials", "key": "nav_assessment"},
        {"name": "Generate Brochure", "icon": "📰", "desc": "Design Course Brochures", "key": "nav_brochure"},
        {"name": "Add Assessment to AP", "icon": "📎", "desc": "Attach Assessments to AP", "key": "nav_annex"},
        {"name": "Check Documents", "icon": "🔍", "desc": "Validate Supporting Documents", "key": "nav_docs"},
    ]

    # First row
    with col1:
        with st.container(border=True):
            st.markdown(f"<div class='card-header'>{modules[0]['icon']} {modules[0]['name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-desc'>{modules[0]['desc']}</div>", unsafe_allow_html=True)
            if st.button("Open", key=modules[0]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate CP"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown(f"<div class='card-header'>{modules[1]['icon']} {modules[1]['name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-desc'>{modules[1]['desc']}</div>", unsafe_allow_html=True)
            if st.button("Open", key=modules[1]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate AP/FG/LG/LP"
                st.rerun()

    with col3:
        with st.container(border=True):
            st.markdown(f"<div class='card-header'>{modules[2]['icon']} {modules[2]['name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-desc'>{modules[2]['desc']}</div>", unsafe_allow_html=True)
            if st.button("Open", key=modules[2]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate Assessment"
                st.rerun()

    # Second row
    col4, col5, col6 = st.columns(3)

    with col4:
        with st.container(border=True):
            st.markdown(f"<div class='card-header'>{modules[3]['icon']} {modules[3]['name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-desc'>{modules[3]['desc']}</div>", unsafe_allow_html=True)
            if st.button("Open", key=modules[3]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate Brochure"
                st.rerun()

    with col5:
        with st.container(border=True):
            st.markdown(f"<div class='card-header'>{modules[4]['icon']} {modules[4]['name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-desc'>{modules[4]['desc']}</div>", unsafe_allow_html=True)
            if st.button("Open", key=modules[4]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Add Assessment to AP"
                st.rerun()

    with col6:
        with st.container(border=True):
            st.markdown(f"<div class='card-header'>{modules[5]['icon']} {modules[5]['name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-desc'>{modules[5]['desc']}</div>", unsafe_allow_html=True)
            if st.button("Open", key=modules[5]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Check Documents"
                st.rerun()

    # Homepage cards end here
    pass

def handle_chat_logic(prompt):
    """Process chat message and get response from AI"""
    if not prompt or not prompt.strip():
        return

    # Add user message to history
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    try:
        from settings.api_manager import load_api_keys
        from agents import Runner

        api_keys = load_api_keys()

        # Get selected model and API provider from session state
        chat_model = st.session_state.get('selected_model')
        api_provider = st.session_state.get('selected_api_provider', 'OPENROUTER')
        api_key = api_keys.get(f"{api_provider}_API_KEY", "")

        if not chat_model:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": "No model selected. Please select a model from the sidebar."
            })
        elif api_key:
            # Import and create the orchestrator
            from courseware_agents.orchestrator import create_orchestrator
            orchestrator = create_orchestrator(model_name=chat_model)

            # Build conversation context from history
            conversation_history = ""
            for msg in st.session_state.chat_messages[:-1]:
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_history += f"{role}: {msg['content']}\n\n"

            # Create the full prompt with context
            full_prompt = f"{conversation_history}User: {prompt}" if conversation_history else prompt

            # Run the orchestrator asynchronously
            async def run_orchestrator():
                result = await Runner.run(orchestrator, full_prompt)
                return result.final_output

            # Execute async function
            with st.spinner("Thinking..."):
                assistant_message = asyncio.run(run_orchestrator())
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

def display_floating_chat():
    """Display the floating chat bubble and window"""
    # Initialize session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_expanded" not in st.session_state:
        st.session_state.chat_expanded = False

    # Floating Bubble (Bottom Right)
    if not st.session_state.chat_expanded:
        st.button("💬", key="chat_bubble_btn")
        if st.session_state.get("chat_bubble_btn"):
            st.session_state.chat_expanded = True
            st.rerun()
    else:
        # Floating Chat Window
        with st.container():
            st.markdown('<div class="chat-window-wrapper">', unsafe_allow_html=True)
            
            # Header in HTML for better control
            st.markdown("""
                <div class="chat-window-header">
                    <span style="font-size: 1.1rem; font-weight: 600;">🤖 Assistant</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Close button (Streamlit)
            col_space, col_close = st.columns([5, 1])
            with col_close:
                if st.button("✖️", key="close_chat_btn"):
                    st.session_state.chat_expanded = False
                    st.rerun()
            
            # Chat messages container
            chat_container = st.container(height=400)
            with chat_container:
                for message in st.session_state.chat_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
            
            # Chat input
            with st.form(key="floating_chat_form", clear_on_submit=True):
                prompt = st.text_input("Ask a question...", label_visibility="collapsed", placeholder="How can I help you?")
                c1, c2 = st.columns([4, 1])
                with c1:
                    submitted = st.form_submit_button("Send", use_container_width=True, type="primary")
                with c2:
                    if st.form_submit_button("🗑️", use_container_width=True, help="Clear History"):
                        st.session_state.chat_messages = []
                        st.rerun()
                
                if submitted and prompt:
                    handle_chat_logic(prompt)
            
            st.markdown('</div>', unsafe_allow_html=True)


st.set_page_config(layout="wide")

# Custom CSS to increase sidebar width and reduce padding
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        min-width: 350px;
        max-width: 350px;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 350px;
    }
    /* Compact sidebar layout */
    [data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 0.3rem;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        margin-bottom: 0.1rem;
        font-size: 0.85rem;
    }
    /* Compact the option menu items */
    [data-testid="stSidebar"] .nav-link {
        padding: 0.4rem 0.8rem !important;
        font-size: 0.9rem !important;
    }
    /* Reduce option menu container padding */
    [data-testid="stSidebar"] .nav {
        gap: 0.1rem !important;
    }
    /* Reduce vertical spacing in sidebar */
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.5rem;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        gap: 0.3rem;
    }
    /* Compact divider above settings */
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
    }

    /* Floating Chat Styles */
    .floating-chat-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
    }
    
    .chat-bubble {
        width: 60px;
        height: 60px;
        background-color: #007bff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 30px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.3s;
    }
    .chat-bubble:hover {
        transform: scale(1.1);
    }
    
    .chat-window {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 400px;
        height: 600px;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 5px 40px rgba(0,0,0,0.2);
        z-index: 10000;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid #eee;
        animation: slideInChat 0.3s ease-out;
    }
    
    @keyframes slideInChat {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .chat-header {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        padding: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 600;
    }

    /* Target the chat window container in Streamlit */
    div[data-testid="stVerticalBlock"] > div:has(.chat-window-content) {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 400px;
        max-height: 600px;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 5px 40px rgba(0,0,0,0.3);
        z-index: 10000;
        display: flex;
        flex-direction: column;
        border: 1px solid #eee;
        padding: 0;
    }

    /* Make the floating button fixed */
    div.stButton > button:has(div p:contains("💬")) {
        position: fixed !important;
        bottom: 20px !important;
        right: 20px !important;
        width: 60px !important;
        height: 60px !important;
        border-radius: 50% !important;
        background-color: #007bff !important;
        color: white !important;
        font-size: 24px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        z-index: 9999 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Target the chat window container more broadly */
    [data-testid="stVerticalBlock"] > div:has(.chat-window-wrapper) {
        position: fixed !important;
        bottom: 90px !important;
        right: 20px !important;
        width: 380px !important;
        background-color: white !important;
        border-radius: 15px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2) !important;
        z-index: 10000 !important;
        padding: 0px !important;
        border: 1px solid #eee !important;
    }

    .chat-window-wrapper {
        display: flex;
        flex-direction: column;
        width: 100%;
    }

    .chat-window-header {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        padding: 12px 15px;
        border-top-left-radius: 15px;
        border-top-right-radius: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
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
    from settings.api_database import get_all_models as db_get_all_models, get_default_model, set_default_model

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

    # Default to OPENROUTER
    if 'selected_api_provider' not in st.session_state:
        st.session_state['selected_api_provider'] = "OPENROUTER"

    # Find index of current provider
    try:
        default_provider_idx = provider_names.index(st.session_state['selected_api_provider'])
    except ValueError:
        default_provider_idx = 0

    # API Provider selector
    selected_provider_idx = st.selectbox(
        "API Provider:",
        range(len(provider_names)),
        format_func=lambda x: provider_display[x],
        index=default_provider_idx,
        help="Select which API key to use for models"
    )
    selected_provider = provider_names[selected_provider_idx]
    st.session_state['selected_api_provider'] = selected_provider

    # Get all models and filter by selected provider (only show enabled models)
    all_db_models = db_get_all_models(include_builtin=True)
    filtered_models = [m for m in all_db_models
                       if m.get("api_provider", "OPENROUTER") == selected_provider
                       and m.get("is_enabled", True)]

    # If no models for this provider, show message
    if not filtered_models:
        st.warning(f"No models configured for {selected_provider}. Add models in Settings → Add Custom Model.")
        model_names = []
        st.session_state['selected_model'] = None
        st.session_state['selected_model_config'] = None
    else:
        model_names = [m["name"] for m in filtered_models]

        # Get default model from database for this provider
        stored_default = get_default_model(selected_provider)

        # Find default model index, or use first available
        default_model_idx = 0
        if stored_default and stored_default in model_names:
            default_model_idx = model_names.index(stored_default)

        # Track provider changes to reset selection
        if 'last_api_provider' not in st.session_state:
            st.session_state['last_api_provider'] = selected_provider

        # When provider changes, reset to that provider's default
        provider_changed = st.session_state['last_api_provider'] != selected_provider
        if provider_changed:
            st.session_state['last_api_provider'] = selected_provider
            # Clear user's explicit selection for this provider
            if 'user_selected_model' in st.session_state:
                del st.session_state['user_selected_model']

        # Determine which model to select:
        # 1. If user explicitly selected a model this session, use it
        # 2. Otherwise, use the default model from database
        if 'user_selected_model' in st.session_state and st.session_state['user_selected_model'] in model_names:
            current_idx = model_names.index(st.session_state['user_selected_model'])
        else:
            current_idx = default_model_idx

        # Model selector with Set Default button
        col_model, col_star = st.columns([5, 1])
        with col_model:
            selected_model_idx = st.selectbox(
                "Select Model:",
                range(len(model_names)),
                format_func=lambda x: model_names[x],
                index=current_idx
            )
        with col_star:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # Spacing
            current_model = model_names[selected_model_idx]
            is_default = stored_default == current_model
            star_icon = "⭐" if is_default else "☆"
            if st.button(star_icon, key="set_default_btn", help="Set as default model for this provider"):
                if not is_default:
                    set_default_model(selected_provider, current_model)
                    # Update user selection to the new default
                    st.session_state['user_selected_model'] = current_model
                    st.rerun()

        # Track user's explicit model selection (only if different from what was shown)
        if model_names[selected_model_idx] != model_names[current_idx]:
            st.session_state['user_selected_model'] = model_names[selected_model_idx]

        # Store selection in session state
        st.session_state['selected_model'] = model_names[selected_model_idx]

        # Get full model config with API key
        all_models = get_all_available_models()
        if model_names[selected_model_idx] in all_models:
            st.session_state['selected_model_config'] = all_models[model_names[selected_model_idx]]
        else:
            st.session_state['selected_model_config'] = None

    # Main features menu (no divider for compact layout)
    menu_options = [
        "Home",
        "Generate CP",
        "Generate AP/FG/LG/LP",
        "Generate Assessment",
        "Generate Brochure",
        "Add Assessment to AP",
        "Check Documents",
    ]

    menu_icons = [
        "house",
        "filetype-doc",
        "file-earmark-richtext",
        "clipboard-check",
        "file-earmark-pdf",
        "folder-symlink",
        "search",
    ]

    # Handle navigation from homepage boxes
    nav_to = st.session_state.get('nav_to', None)
    if nav_to and nav_to in menu_options:
        default_idx = menu_options.index(nav_to)
        st.session_state['nav_to'] = None  # Clear after use
    else:
        default_idx = 0

    selected = option_menu(
        "",  # Title of the sidebar
        menu_options,
        icons=menu_icons,
        menu_icon="boxes",  # Icon for the sidebar title
        default_index=default_idx,  # Default selected item
    )

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

# Always display the floating chat bubble/window
display_floating_chat()
