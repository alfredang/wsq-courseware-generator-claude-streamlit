# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization

# Lazy loading functions for better performance
def lazy_import_assessment():
    import generate_assessment.assessment_generation as assessment_generation
    return assessment_generation

def lazy_import_courseware():
    import generate_ap_fg_lg_lp.courseware_generation as courseware_generation
    return courseware_generation

def lazy_import_brochure_v2():
    import generate_brochure_v2.brochure_generation as brochure_generation
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
        "Generate CP",
        "Generate AP/FG/LG/LP",
        "Generate Assessment",
        "Generate Brochure v2",
        "Add Assessment to AP",
        "Check Documents",
    ]

    menu_icons = [
        "filetype-doc",
        "file-earmark-richtext",
        "clipboard-check",
        "file-earmark-pdf",
        "folder-symlink",
        "search",
    ]

    selected = option_menu(
        "",  # Title of the sidebar
        menu_options,
        icons=menu_icons,
        menu_icon="boxes",  # Icon for the sidebar title
        default_index=0,  # Default selected item
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

# Display the selected app - using lazy loading for performance
if settings_page == "API & LLM Models":
    settings = lazy_import_settings()
    settings.llm_settings_app()
    # Clear settings page when main menu is clicked
    if selected:
        st.session_state['settings_page'] = None

elif settings_page == "Company Management":
    settings = lazy_import_settings()
    settings.company_management_app()
    # Clear settings page when main menu is clicked
    if selected:
        st.session_state['settings_page'] = None

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
