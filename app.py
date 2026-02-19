# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from generate_ap_fg_lg.utils.organizations import get_organizations, get_default_organization


# Lazy loading functions for better performance
def lazy_import_assessment():
    import generate_assessment.assessment_generation as assessment_generation
    return assessment_generation

def lazy_import_courseware():
    import generate_ap_fg_lg.courseware_generation as courseware_generation
    return courseware_generation

def lazy_import_brochure():
    import generate_brochure.brochure_generation as brochure_generation
    return brochure_generation

def lazy_import_docs():
    import courseware_audit.sup_doc as sup_doc
    return sup_doc

def lazy_import_company_settings():
    import company.company_settings as company_settings
    return company_settings

def lazy_import_slides():
    import generate_slides.slides_generation as slides_generation
    return slides_generation

def lazy_import_lesson_plan():
    import generate_lp.lesson_plan_generation as lesson_plan_generation
    return lesson_plan_generation

def lazy_import_extract_course_info():
    import extract_course_info.extract_course_info as extract_course_info
    return extract_course_info


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
</style>
""", unsafe_allow_html=True)

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
    st.markdown("## WSQ Courseware Generator")

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

        # Sync widget key with session state for programmatic updates
        if 'company_selector' not in st.session_state:
            st.session_state['company_selector'] = st.session_state['selected_company_idx']
        elif st.session_state.get('_company_auto_selected'):
            # Auto-select triggered by CP extraction - update widget
            st.session_state['company_selector'] = st.session_state['selected_company_idx']
            st.session_state.pop('_company_auto_selected', None)

        selected_company_idx = st.selectbox(
            "Select Company:",
            range(len(company_names)),
            format_func=lambda x: company_names[x],
            key="company_selector",
        )

        st.session_state['selected_company_idx'] = selected_company_idx
        selected_company = organizations[selected_company_idx]
    else:
        selected_company = default_org
        st.session_state['selected_company_idx'] = 0

    st.session_state['selected_company'] = selected_company

    # Navigation menu
    menu_options = [
        "Extract Course Info",
        "Generate AP/FG/LG",
        "Generate Lesson Plan",
        "Generate Assessment",
        "Generate Slides",
        "Generate Brochure",
        "Courseware Audit",
    ]

    menu_icons = [
        "file-earmark-text",
        "file-earmark-richtext",
        "journal-text",
        "clipboard-check",
        "easel",
        "file-earmark-pdf",
        "search",
    ]

    # Initialize current page
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Extract Course Info"

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

    if st.button("Companies", use_container_width=True):
        if st.session_state.get('settings_page') == "Company Management":
            # Toggle: clicking again exits Company Management
            st.session_state['settings_page'] = None
        else:
            st.session_state['settings_page'] = "Company Management"
        st.rerun()

    # Running agents status
    from utils.agent_status import render_sidebar_agent_status
    render_sidebar_agent_status()

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
page_to_display = st.session_state.get('current_page', 'Extract Course Info')

if settings_page == "Company Management":
    if st.button("← Back to " + page_to_display):
        st.session_state['settings_page'] = None
        st.rerun()
    company_settings = lazy_import_company_settings()
    company_settings.company_management_app()

elif page_to_display == "Extract Course Info":
    st.session_state['settings_page'] = None
    extract_course_info = lazy_import_extract_course_info()
    extract_course_info.app()

elif page_to_display == "Generate AP/FG/LG":
    st.session_state['settings_page'] = None
    courseware_generation = lazy_import_courseware()
    courseware_generation.app()

elif page_to_display == "Generate Lesson Plan":
    st.session_state['settings_page'] = None
    lesson_plan_generation = lazy_import_lesson_plan()
    lesson_plan_generation.app()

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

elif page_to_display == "Courseware Audit":
    st.session_state['settings_page'] = None
    sup_doc = lazy_import_docs()
    sup_doc.app()
