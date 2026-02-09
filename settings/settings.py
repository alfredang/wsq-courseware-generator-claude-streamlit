"""
Settings Management Module

Provides UI for managing Prompt Templates.
All AI processing uses Claude Agent SDK - no API key management needed.
"""

import streamlit as st

from settings.api_database import (
    get_all_prompt_templates,
    get_prompt_template,
    get_prompt_template_by_id,
    update_prompt_template,
    add_prompt_template,
    delete_prompt_template,
    reset_prompt_template_to_default,
)
from settings.admin_auth import is_authenticated, login_page, show_logout_button


def app():
    """Main settings application - Prompt Templates"""
    st.title("Settings")

    # Require authentication
    if not is_authenticated():
        login_page()
        return

    show_logout_button()

    manage_prompt_templates()


def manage_prompt_templates():
    """Manage Prompt Templates section"""
    st.markdown("### Prompt Templates")
    st.caption("Customize the AI prompts used for generating courseware and assessments.")

    # Get all templates
    all_templates = get_all_prompt_templates()

    if not all_templates:
        st.info("No prompt templates found. Templates will be loaded on first use.")
        return

    # Group templates by category
    templates_by_category = {}
    for template in all_templates:
        category = template["category"]
        if category not in templates_by_category:
            templates_by_category[category] = []
        templates_by_category[category].append(template)

    category_icons = {
        "courseware": "📚",
        "brochure": "📰",
        "assessment": "✅",
    }

    category_display_names = {
        "courseware": "Courseware (LG, LP, FG, AP)",
        "brochure": "Brochure",
        "assessment": "Assessment (SAQ, PP, CS, PRJ, ASGN, OI, DEM, RP, OQ)",
    }

    if 'editing_template_id' not in st.session_state:
        st.session_state['editing_template_id'] = None

    for category, templates in sorted(templates_by_category.items()):
        icon = category_icons.get(category, "📋")
        display_name = category_display_names.get(category, category.title())

        with st.expander(f"{icon} {display_name} ({len(templates)} templates)", expanded=True):
            for template in templates:
                template_id = template["id"]
                is_editing = st.session_state['editing_template_id'] == template_id

                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{template['display_name']}**")
                    if template['description']:
                        st.caption(template['description'])

                with col2:
                    st.caption("Built-in" if template['is_builtin'] else "Custom")

                with col3:
                    if is_editing:
                        if st.button("Cancel", key=f"cancel_{template_id}", use_container_width=True):
                            st.session_state['editing_template_id'] = None
                            st.rerun()
                    else:
                        if st.button("Edit", key=f"edit_{template_id}", use_container_width=True):
                            st.session_state['editing_template_id'] = template_id
                            st.rerun()

                if is_editing:
                    st.markdown("---")

                    new_display_name = st.text_input(
                        "Display Name", value=template['display_name'],
                        key=f"name_{template_id}"
                    )
                    new_description = st.text_input(
                        "Description", value=template['description'] or "",
                        key=f"desc_{template_id}"
                    )
                    new_variables = st.text_input(
                        "Variables (comma-separated)", value=template['variables'] or "",
                        key=f"vars_{template_id}",
                        help="Template variables like: schema, course_title"
                    )
                    new_content = st.text_area(
                        "Prompt Content", value=template['content'],
                        height=400, key=f"content_{template_id}"
                    )

                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])

                    with btn_col1:
                        if st.button("Save", key=f"save_{template_id}", type="primary", use_container_width=True):
                            if update_prompt_template(
                                template_id, content=new_content,
                                display_name=new_display_name,
                                description=new_description, variables=new_variables
                            ):
                                st.success("Template saved!")
                                st.session_state['editing_template_id'] = None
                                st.rerun()
                            else:
                                st.error("Failed to save template")

                    with btn_col2:
                        if template['is_builtin']:
                            if st.button("Reset", key=f"reset_{template_id}", use_container_width=True):
                                if reset_prompt_template_to_default(template_id):
                                    st.success("Template reset!")
                                    st.session_state['editing_template_id'] = None
                                    st.rerun()
                        else:
                            if st.button("Delete", key=f"delete_{template_id}", use_container_width=True):
                                if delete_prompt_template(template_id):
                                    st.success("Template deleted!")
                                    st.session_state['editing_template_id'] = None
                                    st.rerun()

                    st.markdown("---")
                else:
                    preview = template['content'][:150]
                    if len(template['content']) > 150:
                        preview += "..."
                    st.code(preview, language="markdown")

    st.markdown("---")

    # Add new template
    with st.expander("Add New Prompt Template", expanded=False):
        new_category = st.selectbox(
            "Category",
            options=["courseware", "brochure", "assessment"],
            format_func=lambda x: category_display_names.get(x, x.title()),
            key="new_template_category"
        )
        new_name = st.text_input("Template Name", placeholder="e.g., custom_generation", key="new_template_name")
        new_display = st.text_input("Display Name", placeholder="e.g., Custom Generation", key="new_template_display")
        new_desc = st.text_input("Description", key="new_template_desc")
        new_vars = st.text_input("Variables (comma-separated)", key="new_template_vars")
        new_content = st.text_area("Prompt Content", height=200, key="new_template_content")

        if st.button("Add Template", type="primary"):
            if not new_name or not new_display or not new_content:
                st.error("Name, Display Name, and Content are required")
            else:
                if add_prompt_template(
                    category=new_category,
                    name=new_name.lower().replace(" ", "_"),
                    display_name=new_display,
                    content=new_content,
                    description=new_desc,
                    variables=new_vars
                ):
                    st.success(f"Template '{new_display}' added!")
                    st.rerun()
                else:
                    st.error("Failed to add template")
