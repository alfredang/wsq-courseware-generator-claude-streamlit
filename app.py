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
        </style>
        """, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>WSQ Courseware Generator with OpenAI Multi Agents</h1>", unsafe_allow_html=True)


    st.markdown("---")


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
            st.markdown(f"### {modules[0]['icon']} {modules[0]['name']}")
            st.caption(modules[0]['desc'])
            if st.button("Open", key=modules[0]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate CP"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown(f"### {modules[1]['icon']} {modules[1]['name']}")
            st.caption(modules[1]['desc'])
            if st.button("Open", key=modules[1]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate AP/FG/LG/LP"
                st.rerun()

    with col3:
        with st.container(border=True):
            st.markdown(f"### {modules[2]['icon']} {modules[2]['name']}")
            st.caption(modules[2]['desc'])
            if st.button("Open", key=modules[2]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate Assessment"
                st.rerun()

    # Second row
    col4, col5, col6 = st.columns(3)

    with col4:
        with st.container(border=True):
            st.markdown(f"### {modules[3]['icon']} {modules[3]['name']}")
            st.caption(modules[3]['desc'])
            if st.button("Open", key=modules[3]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Generate Brochure v2"
                st.rerun()

    with col5:
        with st.container(border=True):
            st.markdown(f"### {modules[4]['icon']} {modules[4]['name']}")
            st.caption(modules[4]['desc'])
            if st.button("Open", key=modules[4]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Add Assessment to AP"
                st.rerun()

    with col6:
        with st.container(border=True):
            st.markdown(f"### {modules[5]['icon']} {modules[5]['name']}")
            st.caption(modules[5]['desc'])
            if st.button("Open", key=modules[5]['key'], use_container_width=True):
                st.session_state['nav_to'] = "Check Documents"
                st.rerun()

    # Chat section header
    st.markdown("### Chat with Courseware Orchestrator")
    st.caption("Ask questions or request help with courseware generation")

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about courseware generation or request help..."):
        # Add user message to history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        # Get response from AI using the Orchestrator agent
        try:
            from settings.api_manager import load_api_keys
            from agents import Runner

            api_keys = load_api_keys()
            openrouter_key = api_keys.get("OPENROUTER_API_KEY", "")

            if openrouter_key:
                # Import and create the orchestrator
                from courseware_agents.orchestrator import create_orchestrator

                # Get selected model from session state (default to GPT-4o for orchestrator)
                chat_model = st.session_state.get('selected_model', 'GPT-4o')

                # Create orchestrator with handoffs to specialized agents
                orchestrator = create_orchestrator(model_name=chat_model)

                # Build conversation context from history
                conversation_history = ""
                for msg in st.session_state.chat_messages[:-1]:  # Exclude the current message
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
                    "content": "OpenRouter API key not configured. Please set up your OPENROUTER_API_KEY in Settings > API & Models to use the orchestrator agent."
                })
        except ImportError as e:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"Agent module not found. Please ensure the courseware_agents package is properly installed. Error: {str(e)}"
            })
        except Exception as e:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"Error connecting to AI service: {str(e)}"
            })

        st.rerun()

    # Clear chat button
    if st.session_state.chat_messages:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()


st.set_page_config(layout="wide")

# Custom CSS to increase sidebar width
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        min-width: 350px;
        max-width: 350px;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 350px;
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

    # Model Selection
    st.markdown("---")
    from settings.api_manager import get_all_available_models
    all_models = get_all_available_models()
    model_names = list(all_models.keys())

    # Find default model index (DeepSeek-V3.1 or first available)
    default_model_idx = 0
    for i, name in enumerate(model_names):
        if "deepseek" in name.lower() and "v3" in name.lower():
            default_model_idx = i
            break

    # Use default on first load, then respect user selection
    if 'selected_model_idx' not in st.session_state:
        st.session_state['selected_model_idx'] = default_model_idx

    # Validate stored index
    if st.session_state['selected_model_idx'] >= len(model_names):
        st.session_state['selected_model_idx'] = default_model_idx

    selected_model_idx = st.selectbox(
        "Select Model:",
        range(len(model_names)),
        format_func=lambda x: model_names[x],
        index=st.session_state['selected_model_idx']
    )

    # Store selection in session state
    st.session_state['selected_model_idx'] = selected_model_idx
    st.session_state['selected_model'] = model_names[selected_model_idx]
    st.session_state['selected_model_config'] = all_models[model_names[selected_model_idx]]

    st.markdown("---")

    # Main features menu
    menu_options = [
        "Home",
        "Generate CP",
        "Generate AP/FG/LG/LP",
        "Generate Assessment",
        "Generate Brochure v2",
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

    # Separate Settings section using buttons
    st.markdown("---")
    st.markdown("##### Settings")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("API & Models", use_container_width=True):
            st.session_state['settings_page'] = "API & LLM Models"
    with col2:
        if st.button("Companies", use_container_width=True):
            st.session_state['settings_page'] = "Company Management"

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

elif selected == "Generate Brochure v2":
    st.session_state['settings_page'] = None
    brochure_generation = lazy_import_brochure_v2()
    brochure_generation.app()

elif selected == "Add Assessment to AP":
    st.session_state['settings_page'] = None
    annex_assessment_v2 = lazy_import_annex_v2()
    annex_assessment_v2.app()
