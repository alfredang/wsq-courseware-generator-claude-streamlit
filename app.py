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

def lazy_import_brochure():
    import generate_brochure.brochure_generation as brochure_generation
    return brochure_generation

def lazy_import_annex():
    import add_assessment_to_ap.annex_assessment_v2 as annex_assessment_v2
    return annex_assessment_v2

def lazy_import_docs():
    import check_documents.sup_doc as sup_doc
    return sup_doc

def lazy_import_company_settings():
    import company.company_settings as company_settings
    return company_settings

def lazy_import_slides():
    import generate_slides.slides_generation as slides_generation
    return slides_generation

def lazy_import_lesson_plan():
    import generate_ap_fg_lg_lp.lesson_plan_generation as lesson_plan_generation
    return lesson_plan_generation


def display_homepage():
    """Display homepage with navigation boxes"""
    st.markdown("""
        <style>
            .block-container { padding-top: 1rem; }
            .card-header { text-align: center; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; }
            .card-desc { text-align: center; font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-size: 1.75rem;'>WSQ Courseware Generator with Claude Code</h2>", unsafe_allow_html=True)

    modules = [
        {"name": "Generate AP/FG/LG", "icon": "📚", "desc": "Generate Courseware Documents", "menu": "Generate AP/FG/LG"},
        {"name": "Generate Lesson Plan", "icon": "📋", "desc": "Generate Lesson Plan with Schedule", "menu": "Generate Lesson Plan"},
        {"name": "Generate Assessment", "icon": "✅", "desc": "Create Assessment Materials", "menu": "Generate Assessment"},
        {"name": "Generate Slides", "icon": "🎯", "desc": "Create Presentation Slides", "menu": "Generate Slides"},
        {"name": "Generate Brochure", "icon": "📰", "desc": "Design Course Brochures", "menu": "Generate Brochure"},
        {"name": "Add Assessment to AP", "icon": "📎", "desc": "Attach Assessments to AP", "menu": "Add Assessment to AP"},
        {"name": "Courseware Audit", "icon": "🔍", "desc": "Validate Supporting Documents", "menu": "Courseware Audit"},
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

# Default model - uses Claude Code subscription
if 'selected_model' not in st.session_state:
    st.session_state['selected_model'] = "default"

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

    # Navigation menu
    menu_options = [
        "Home",
        "Generate AP/FG/LG",
        "Generate Lesson Plan",
        "Generate Assessment",
        "Generate Slides",
        "Generate Brochure",
        "Add Assessment to AP",
        "Courseware Audit",
    ]

    menu_icons = [
        "house",
        "file-earmark-richtext",
        "journal-text",
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

if settings_page == "Company Management":
    company_settings = lazy_import_company_settings()
    company_settings.company_management_app()

elif page_to_display == "Home":
    st.session_state['settings_page'] = None
    display_homepage()

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

elif page_to_display == "Add Assessment to AP":
    st.session_state['settings_page'] = None
    annex_assessment = lazy_import_annex()
    annex_assessment.app()

elif page_to_display == "Courseware Audit":
    st.session_state['settings_page'] = None
    sup_doc = lazy_import_docs()
    sup_doc.app()
