# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization
import os


# Lazy loading functions for better performance
def lazy_import_assessment():
    import generate_assessment.assessment_generation as assessment_generation
    return assessment_generation

def lazy_import_courseware():
    import generate_ap_fg_lg_lp.courseware_generation as courseware_generation
    return courseware_generation

def lazy_import_brochure():
    import generate_brochure.brochure_generation as brochure_generation
    return brochure_generation

def lazy_import_annex():
    import add_assessment_to_ap.annex_assessment_v2 as annex_assessment_v2
    return annex_assessment_v2

def lazy_import_course_proposal():
    import generate_cp.app as course_proposal_app
    return course_proposal_app

def lazy_import_docs():
    import check_documents.sup_doc as sup_doc
    return sup_doc

def lazy_import_settings():
    import settings.settings as settings_module
    return settings_module

def lazy_import_company_settings():
    import company.company_settings as company_settings
    return company_settings

def lazy_import_slides():
    import generate_slides.slides_generation as slides_generation
    return slides_generation


def display_homepage():
    """Display homepage with navigation boxes"""
    st.markdown("""
        <style>
            .block-container { padding-top: 1rem; }
            .card-header { text-align: center; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; }
            .card-desc { text-align: center; font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-size: 1.75rem;'>WSQ Courseware Assistant with Claude Agents</h2>", unsafe_allow_html=True)

    modules = [
        {"name": "Generate CP", "icon": "📄", "desc": "Create Course Proposals", "menu": "Generate CP"},
        {"name": "Generate AP/FG/LG/LP", "icon": "📚", "desc": "Generate Courseware Documents", "menu": "Generate AP/FG/LG/LP"},
        {"name": "Generate Assessment", "icon": "✅", "desc": "Create Assessment Materials", "menu": "Generate Assessment"},
        {"name": "Generate Slides", "icon": "🎯", "desc": "Create Presentation Slides", "menu": "Generate Slides"},
        {"name": "Generate Brochure", "icon": "📰", "desc": "Design Course Brochures", "menu": "Generate Brochure"},
        {"name": "Add Assessment to AP", "icon": "📎", "desc": "Attach Assessments to AP", "menu": "Add Assessment to AP"},
        {"name": "Check Documents", "icon": "🔍", "desc": "Validate Supporting Documents", "menu": "Check Documents"},
    ]

    for i in range(0, len(modules), 2):
        col1, col2 = st.columns(2)

        with col1:
            m = modules[i]
            with st.container(border=True):
                st.markdown(f"<div class='card-header'>{m['icon']} {m['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-desc'>{m['desc']}</div>", unsafe_allow_html=True)
                if st.button("Open", key=f"nav_{i}", use_container_width=True):
                    st.session_state['current_page'] = m['menu']
                    st.session_state['settings_page'] = None
                    st.rerun()

        with col2:
            if i + 1 < len(modules):
                m = modules[i + 1]
                with st.container(border=True):
                    st.markdown(f"<div class='card-header'>{m['icon']} {m['name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-desc'>{m['desc']}</div>", unsafe_allow_html=True)
                    if st.button("Open", key=f"nav_{i+1}", use_container_width=True):
                        st.session_state['current_page'] = m['menu']
                        st.session_state['settings_page'] = None
                        st.rerun()


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(layout="wide")

# Global CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] { min-width: 350px; max-width: 350px; }
    [data-testid="stSidebar"] > div:first-child { width: 350px; }
    [data-testid="stSidebar"] hr { margin: 0.5rem 0 !important; }
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

# Ensure built-in models are always up to date
if 'models_refreshed' not in st.session_state:
    try:
        from settings.api_database import refresh_builtin_models
        refresh_builtin_models()
        st.session_state['models_refreshed'] = True
    except Exception:
        pass

# Get organizations - cached
@st.cache_data
def get_cached_organizations():
    return get_organizations()

@st.cache_data
def get_cached_default_organization():
    return get_default_organization()

organizations = get_cached_organizations()
default_org = get_cached_default_organization()

# =============================================================================
# Sidebar
# =============================================================================

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

        if 'selected_company_idx' not in st.session_state:
            st.session_state['selected_company_idx'] = default_company_idx

        # Validate stored index
        if st.session_state['selected_company_idx'] >= len(organizations):
            st.session_state['selected_company_idx'] = default_company_idx

        selected_company_idx = st.selectbox(
            "Select Company:",
            range(len(company_names)),
            format_func=lambda x: company_names[x],
            index=st.session_state['selected_company_idx']
        )

        st.session_state['selected_company_idx'] = selected_company_idx
        selected_company = organizations[selected_company_idx]
    else:
        selected_company = default_org
        st.session_state['selected_company_idx'] = 0

    st.session_state['selected_company'] = selected_company

    # Model Selection
    from settings.api_manager import get_all_available_models, get_all_api_key_configs, load_api_keys
    from settings.api_database import get_all_models as db_get_all_models, get_task_model_assignment

    # Mapping from menu names to task IDs
    MENU_TO_TASK_ID = {
        "Home": "global",
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

    # Build API provider options
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

    all_providers = configured_providers + unconfigured_providers
    provider_names = [p[0] for p in all_providers]
    provider_display = [p[1] for p in all_providers]

    # Check if current menu has a model assignment
    current_menu = st.session_state.get('previous_menu_selection', 'Home')
    task_id = MENU_TO_TASK_ID.get(current_menu, None)
    task_assignment = get_task_model_assignment(task_id) if task_id else None

    # Fallback to Global Default
    if not task_assignment:
        task_assignment = get_task_model_assignment("global")

    if task_assignment:
        assigned_provider = task_assignment.get("api_provider", "ANTHROPIC")
        assigned_model = task_assignment.get("model_name", "")
        st.session_state['selected_api_provider'] = assigned_provider
        st.session_state['assigned_model_for_task'] = assigned_model
    else:
        if 'selected_api_provider' not in st.session_state:
            st.session_state['selected_api_provider'] = "ANTHROPIC"
        if 'assigned_model_for_task' in st.session_state:
            del st.session_state['assigned_model_for_task']

    # Find index of current provider
    try:
        default_provider_idx = provider_names.index(st.session_state['selected_api_provider'])
    except ValueError:
        default_provider_idx = 0

    if provider_names:
        selected_provider_idx = st.selectbox(
            "API Provider:",
            range(len(provider_names)),
            format_func=lambda x: provider_display[x],
            index=default_provider_idx,
            help="Select which API key to use" + (" (Set by Model Assignment)" if task_assignment else ""),
            disabled=bool(task_assignment)
        )
        selected_provider = provider_names[selected_provider_idx]
        if not task_assignment:
            st.session_state['selected_api_provider'] = selected_provider

    # Get models filtered by provider
    all_db_models = db_get_all_models(include_builtin=True)
    filtered_models = [m for m in all_db_models
                       if m.get("api_provider", "ANTHROPIC") == st.session_state['selected_api_provider']
                       and m.get("is_enabled", True)]

    if not filtered_models:
        st.warning(f"No models configured for {st.session_state['selected_api_provider']}. Add models in Settings.")
        model_names = []
        st.session_state['selected_model'] = None
        st.session_state['selected_model_config'] = None
    else:
        model_names = [m["name"] for m in filtered_models]

        if task_assignment and st.session_state.get('assigned_model_for_task') in model_names:
            current_idx = model_names.index(st.session_state['assigned_model_for_task'])
        elif 'user_selected_model' in st.session_state and st.session_state['user_selected_model'] in model_names:
            current_idx = model_names.index(st.session_state['user_selected_model'])
        else:
            current_idx = 0

        selected_model_idx = st.selectbox(
            "Select Model:",
            range(len(model_names)),
            format_func=lambda x: model_names[x],
            index=current_idx,
            disabled=bool(task_assignment)
        )

        if not task_assignment and model_names[selected_model_idx] != model_names[current_idx]:
            st.session_state['user_selected_model'] = model_names[selected_model_idx]

        st.session_state['selected_model'] = model_names[selected_model_idx]

        all_models = get_all_available_models()
        if model_names[selected_model_idx] in all_models:
            st.session_state['selected_model_config'] = all_models[model_names[selected_model_idx]]
        else:
            st.session_state['selected_model_config'] = None

    if task_assignment:
        st.caption(f"📌 Using assigned model for {current_menu}")

    # Navigation menu
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

    # Initialize current page
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Home"

    current_page = st.session_state['current_page']
    if current_page in menu_options:
        default_idx = menu_options.index(current_page)
    else:
        default_idx = 0

    selected = option_menu(
        "",
        menu_options,
        icons=menu_icons,
        menu_icon="boxes",
        default_index=default_idx,
        key="main_nav_menu"
    )

    # Update current page when menu selection changes
    if selected != current_page:
        st.session_state['current_page'] = selected
        st.session_state['settings_page'] = None
        current_page = selected
        st.rerun()

    # Settings section
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; font-weight: 600; margin-bottom: 0.3rem;'>Settings</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("API & Models", use_container_width=True):
            st.session_state['settings_page'] = "API & LLM Models"
            st.rerun()
    with col2:
        if st.button("Companies", use_container_width=True):
            st.session_state['settings_page'] = "Company Management"
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #888; font-size: 0.8rem;'>
            Powered by <b>Tertiary Infotech Academy Pte Ltd</b>
        </div>
    """, unsafe_allow_html=True)

# =============================================================================
# Menu change tracking
# =============================================================================

previous_menu = st.session_state.get('previous_menu_selection', None)
menu_changed = previous_menu is not None and previous_menu != selected
st.session_state['previous_menu_selection'] = selected

if menu_changed:
    st.session_state['settings_page'] = None
    st.rerun()

# =============================================================================
# Page Routing
# =============================================================================

settings_page = st.session_state.get('settings_page', None)
page_to_display = st.session_state.get('current_page', 'Home')

if settings_page == "API & LLM Models":
    settings_mod = lazy_import_settings()
    settings_mod.llm_settings_app()

elif settings_page == "Company Management":
    company_settings = lazy_import_company_settings()
    company_settings.company_management_app()

elif page_to_display == "Home":
    st.session_state['settings_page'] = None
    display_homepage()

elif page_to_display == "Generate CP":
    st.session_state['settings_page'] = None
    course_proposal_app = lazy_import_course_proposal()
    course_proposal_app.app()

elif page_to_display == "Generate AP/FG/LG/LP":
    st.session_state['settings_page'] = None
    courseware_generation = lazy_import_courseware()
    courseware_generation.app()

elif page_to_display == "Generate Assessment":
    st.session_state['settings_page'] = None
    assessment_generation = lazy_import_assessment()
    assessment_generation.app()

elif page_to_display == "Generate Slides":
    st.session_state['settings_page'] = None
    slides_generation = lazy_import_slides()
    slides_generation.app()

elif page_to_display == "Generate Brochure":
    st.session_state['settings_page'] = None
    brochure_generation = lazy_import_brochure()
    brochure_generation.app()

elif page_to_display == "Add Assessment to AP":
    st.session_state['settings_page'] = None
    annex_assessment = lazy_import_annex()
    annex_assessment.app()

elif page_to_display == "Check Documents":
    st.session_state['settings_page'] = None
    sup_doc = lazy_import_docs()
    sup_doc.app()
