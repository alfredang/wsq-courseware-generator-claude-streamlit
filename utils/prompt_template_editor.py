"""
Reusable Prompt Template Editor Component

Renders prompt templates for a given category as collapsible, editable
text areas on any Streamlit page. Templates are loaded from and saved
to the SQLite database.
"""

import streamlit as st
from settings.api_database import (
    get_prompt_templates_by_category,
    get_prompt_template_by_id,
    update_prompt_template,
    reset_prompt_template_to_default,
)


def render_prompt_templates(category: str, label: str = "Prompt Templates"):
    """
    Render editable prompt templates for a category as a collapsible section.

    Args:
        category: Template category (e.g. 'courseware', 'assessment', 'brochure')
        label: Display label for the expander
    """
    templates = get_prompt_templates_by_category(category)
    if not templates:
        return

    with st.expander(f"{label} ({len(templates)})", expanded=False):
        for template in templates:
            template_id = template["id"]
            key_prefix = f"tpl_{category}_{template_id}"

            st.markdown(f"**{template['display_name']}**")
            if template["description"]:
                st.caption(template["description"])

            new_content = st.text_area(
                "Prompt:",
                value=template["content"],
                height=250,
                key=f"{key_prefix}_content",
                label_visibility="collapsed",
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Save", key=f"{key_prefix}_save", use_container_width=True):
                    if update_prompt_template(template_id, content=new_content):
                        st.success("Saved!")
                        st.rerun()
                    else:
                        st.error("Failed to save")
            with col2:
                if template["is_builtin"]:
                    if st.button("Reset", key=f"{key_prefix}_reset", use_container_width=True):
                        if reset_prompt_template_to_default(template_id):
                            st.success("Reset to default!")
                            st.rerun()

            st.markdown("---")
