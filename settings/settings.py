"""
Settings Management Module

This module provides UI for managing LLM Models and API Keys.
All models (built-in + custom) are stored in SQLite database.

Author: Wong Xin Ping
Date: 18 September 2025
Updated: 26 January 2026
"""

import streamlit as st
import requests
from typing import Dict, List, Any

# Import API management functions
from settings.api_manager import (
    load_api_keys,
    save_api_keys,
    load_custom_models,
    load_builtin_models,
    add_custom_model,
    remove_custom_model,
    delete_api_key,
    get_all_available_models,
    # API key config functions
    get_all_api_key_configs,
    add_api_key_config,
    remove_api_key_config,
    get_api_providers_for_dropdown
)
from settings.api_database import (
    refresh_builtin_models,
    refresh_builtin_api_keys,
    set_model_enabled,
    get_all_models as db_get_all_models,
    get_enabled_models_by_provider,
    AVAILABLE_TASKS,
    get_all_task_model_assignments,
    set_task_model_assignment,
    # Prompt template functions
    get_all_prompt_templates,
    get_prompt_templates_by_category,
    get_prompt_template,
    get_prompt_template_by_id,
    update_prompt_template,
    add_prompt_template,
    delete_prompt_template,
    reset_prompt_template_to_default,
    get_prompt_template_categories,
)
from settings.admin_auth import is_authenticated, login_page, show_logout_button


def app():
    """Main settings application - API & LLM Models only"""
    st.title("Settings")

    # Require authentication
    if not is_authenticated():
        login_page()
        return

    # Show logout button
    show_logout_button()

    # Force refresh of models on settings page load
    if st.button("Refresh Models", help="Click to refresh the model list"):
        # Refresh built-in models and API keys from code
        refresh_builtin_models()
        refresh_builtin_api_keys()
        # Clear relevant session state
        if 'custom_models' in st.session_state:
            del st.session_state['custom_models']
        if 'api_keys' in st.session_state:
            del st.session_state['api_keys']
        if 'all_models' in st.session_state:
            del st.session_state['all_models']
        st.success("Models and API configurations refreshed!")
        st.rerun()

    # API & LLM Models section
    st.subheader("API & LLM Models")
    manage_llm_settings()


def llm_settings_app():
    """API & LLM Models page"""
    st.title("API & LLM Models")

    # Require authentication
    if not is_authenticated():
        login_page()
        return

    # Show logout button
    show_logout_button()

    manage_llm_settings()


def manage_llm_settings():
    """Manage LLM Models and API Keys"""

    # Initialize view state
    if 'llm_settings_view' not in st.session_state:
        st.session_state['llm_settings_view'] = 'api_keys'

    # View selector using columns with buttons (like Company Management)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔑 API Keys", use_container_width=True,
                     type="primary" if st.session_state['llm_settings_view'] == 'api_keys' else "secondary"):
            st.session_state['llm_settings_view'] = 'api_keys'
            st.rerun()
    with col2:
        if st.button("📋 All Models", use_container_width=True,
                     type="primary" if st.session_state['llm_settings_view'] == 'all_models' else "secondary"):
            st.session_state['llm_settings_view'] = 'all_models'
            st.rerun()
    with col3:
        if st.button("⚙️ Model Assignments", use_container_width=True,
                     type="primary" if st.session_state['llm_settings_view'] == 'update_models' else "secondary"):
            st.session_state['llm_settings_view'] = 'update_models'
            st.rerun()
    with col4:
        if st.button("📝 Prompt Templates", use_container_width=True,
                     type="primary" if st.session_state['llm_settings_view'] == 'prompt_templates' else "secondary"):
            st.session_state['llm_settings_view'] = 'prompt_templates'
            st.rerun()

    st.markdown("---")

    # Display based on current view
    if st.session_state['llm_settings_view'] == 'api_keys':
        manage_api_keys()
    elif st.session_state['llm_settings_view'] == 'all_models':
        display_all_models()
    elif st.session_state['llm_settings_view'] == 'update_models':
        update_models_from_provider()
    elif st.session_state['llm_settings_view'] == 'prompt_templates':
        manage_prompt_templates()


def update_secrets_toml(key_name: str, key_value: str) -> bool:
    """Update or add an API key in .streamlit/secrets.toml"""
    import os

    secrets_path = ".streamlit/secrets.toml"

    try:
        # Create .streamlit directory if it doesn't exist
        os.makedirs(".streamlit", exist_ok=True)

        # Read existing content
        existing_content = {}
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                content = f.read()
                # Parse existing keys
                for line in content.strip().split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        k, v = line.split('=', 1)
                        existing_content[k.strip()] = v.strip().strip('"').strip("'")

        # Update or add the key
        existing_content[key_name] = key_value

        # Write back to file
        with open(secrets_path, 'w') as f:
            for k, v in existing_content.items():
                f.write(f'{k} = "{v}"\n')

        return True
    except Exception as e:
        st.error(f"Error updating secrets.toml: {e}")
        return False


def manage_api_keys():
    """Manage API Keys section"""
    st.markdown("### Existing API Keys")

    # Load current API keys and configurations
    current_keys = load_api_keys()
    api_key_configs = get_all_api_key_configs()

    # Initialize visibility state for password fields
    if 'api_key_visibility' not in st.session_state:
        st.session_state['api_key_visibility'] = {}

    # Initialize edited values state
    if 'api_key_edits' not in st.session_state:
        st.session_state['api_key_edits'] = {}

    # Track if any changes were made
    has_changes = False

    # Display each API key with password input
    for config in api_key_configs:
        key_name = config["key_name"]
        display_name = config["display_name"]
        key_value = current_keys.get(key_name, "")
        is_builtin = config.get("is_builtin", True)

        # Initialize visibility state for this key
        if key_name not in st.session_state['api_key_visibility']:
            st.session_state['api_key_visibility'][key_name] = False

        # Get current visibility
        show_password = st.session_state['api_key_visibility'][key_name]

        col1, col2, col3, col4 = st.columns([2, 3, 0.5, 0.5])

        with col1:
            st.markdown(f"**{key_name}**")

        with col2:
            # Password input field
            input_type = "default" if show_password else "password"
            new_value = st.text_input(
                f"API Key for {key_name}",
                value=key_value,
                type=input_type,
                key=f"input_{key_name}",
                placeholder="Enter API key...",
                label_visibility="collapsed"
            )

            # Track changes
            if new_value != key_value:
                st.session_state['api_key_edits'][key_name] = new_value
                has_changes = True

        with col3:
            # Eye icon to toggle visibility
            eye_icon = "👁️" if show_password else "👁️‍🗨️"
            if st.button(eye_icon, key=f"toggle_{key_name}", help="Show/Hide"):
                st.session_state['api_key_visibility'][key_name] = not show_password
                st.rerun()

        with col4:
            # Trash icon to delete (only for custom API keys)
            if not is_builtin:
                if st.button("🗑️", key=f"delete_{key_name}", help="Delete"):
                    if remove_api_key_config(key_name):
                        st.success(f"Deleted {key_name}")
                        st.rerun()

    st.markdown("---")

    # Save All Changes button
    if st.button("💾 Save All Changes", type="primary", use_container_width=True):
        saved_count = 0
        for key_name, new_value in st.session_state.get('api_key_edits', {}).items():
            if new_value:
                if update_secrets_toml(key_name, new_value):
                    saved_count += 1

        if saved_count > 0:
            st.success(f"Saved {saved_count} API key(s)!")
            # Clear caches
            st.session_state['api_key_edits'] = {}
            if 'api_keys' in st.session_state:
                del st.session_state['api_keys']
            st.rerun()
        else:
            st.info("No changes to save")



def display_all_models():
    """Display all models from database (built-in + custom) with selection and default controls"""
    from settings.api_database import get_all_models as db_get_all_models

    # Get all models from database (including is_enabled status)
    all_db_models = db_get_all_models(include_builtin=True)

    if not all_db_models:
        st.info("No models available. Go to **Update Models** tab to fetch and add models from API providers.")
        return

    # Group models by API provider
    models_by_provider = {}
    for model in all_db_models:
        api_provider = model.get("api_provider", "OPENROUTER")
        if api_provider not in models_by_provider:
            models_by_provider[api_provider] = []
        models_by_provider[api_provider].append(model)

    # Define provider display order
    provider_order = ["OPENROUTER", "OPENAI", "ANTHROPIC", "GEMINI", "DEEPSEEK", "GROQ", "GROK"]
    sorted_providers = sorted(models_by_provider.keys(), key=lambda x: provider_order.index(x) if x in provider_order else 999)

    # Filter by API Provider dropdown
    st.markdown("**Filter by API Provider**")
    available_providers = ["All Providers"] + sorted_providers
    selected_filter = st.selectbox(
        "Filter by API Provider",
        options=available_providers,
        index=0,
        key="model_provider_filter",
        label_visibility="collapsed"
    )

    # Display models grouped by provider
    if selected_filter == "All Providers":
        total_models = sum(len(models) for models in models_by_provider.values())
        st.caption(f"{total_models} models available")
        providers_to_show = sorted_providers
    else:
        total_models = len(models_by_provider.get(selected_filter, []))
        st.caption(f"{total_models} models from {selected_filter}")
        providers_to_show = [selected_filter]

    for provider in providers_to_show:
        models = models_by_provider.get(provider, [])
        if models:
            with st.expander(f"{provider} ({len(models)} models)", expanded=(len(providers_to_show) == 1)):
                # Header row
                hcol1, hcol2, hcol3, hcol4 = st.columns([3, 3, 1.5, 1])
                with hcol1:
                    st.markdown("**Model**")
                with hcol2:
                    st.markdown("**ID**")
                with hcol3:
                    st.markdown("**Temp**")
                with hcol4:
                    st.markdown("**Selected**")

                # Model rows
                for idx, model in enumerate(models):
                    model_name = model["name"]
                    model_id = model["config"].get("model", "N/A")
                    temp = model["config"].get("temperature", 0.2)
                    is_enabled = model.get("is_enabled", True)

                    col1, col2, col3, col4 = st.columns([3, 3, 1.5, 1])

                    with col1:
                        st.markdown(f"{model_name}")
                    with col2:
                        st.markdown(f"`{model_id}`")
                    with col3:
                        st.markdown(f"{temp}")
                    with col4:
                        # Selected checkbox
                        new_enabled = st.checkbox(
                            "",
                            value=is_enabled,
                            key=f"sel_{provider}_{idx}",
                            label_visibility="collapsed"
                        )
                        if new_enabled != is_enabled:
                            set_model_enabled(model_name, new_enabled)
                            st.rerun()

    # Remove custom models section
    custom_models = load_custom_models()
    if custom_models:
        st.write("### Remove Custom Models")
        for model in custom_models:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{model['name']}** - `{model['config']['model']}`")
            with col2:
                if st.button("Remove", key=f"remove_{model['name']}"):
                    if remove_custom_model(model['name']):
                        st.success(f"Model '{model['name']}' removed!")
                        if 'custom_models' in st.session_state:
                            del st.session_state['custom_models']
                        st.rerun()
                    else:
                        st.error("Error removing model")


def _get_model_sort_key(model_id: str) -> tuple:
    """
    Generate a sort key for model IDs to sort from newest to oldest.
    Higher versions and newer models come first.
    """
    import re
    model_id_lower = model_id.lower()

    # Priority tiers (lower number = higher priority/newer)
    tier = 99

    # GPT models - prioritize by version
    if "gpt-5.2" in model_id_lower:
        tier = 1
    elif "gpt-5.1" in model_id_lower:
        tier = 2
    elif "gpt-5" in model_id_lower and "gpt-5." not in model_id_lower:
        tier = 3
    elif "gpt-4.1" in model_id_lower:
        tier = 4
    elif "gpt-4o" in model_id_lower:
        tier = 5
    elif "gpt-4-turbo" in model_id_lower:
        tier = 6
    elif "gpt-4" in model_id_lower:
        tier = 7
    elif "o4" in model_id_lower:
        tier = 8
    elif "o3" in model_id_lower:
        tier = 9
    elif "o1" in model_id_lower:
        tier = 10
    elif "chatgpt" in model_id_lower:
        tier = 15
    elif "gpt-3" in model_id_lower:
        tier = 20

    # Claude models
    elif "claude-opus-4.5" in model_id_lower or "claude-4.5" in model_id_lower:
        tier = 1
    elif "claude-sonnet-4.5" in model_id_lower:
        tier = 2
    elif "claude-opus-4" in model_id_lower or "claude-4" in model_id_lower:
        tier = 3
    elif "claude-sonnet-4" in model_id_lower:
        tier = 4
    elif "claude-3.5" in model_id_lower:
        tier = 5
    elif "claude-3" in model_id_lower:
        tier = 6

    # Gemini models
    elif "gemini-3" in model_id_lower:
        tier = 1
    elif "gemini-2.5" in model_id_lower:
        tier = 2
    elif "gemini-2" in model_id_lower:
        tier = 3
    elif "gemini-1.5" in model_id_lower:
        tier = 4
    elif "gemini" in model_id_lower:
        tier = 5

    # Extract date from model ID if present (e.g., 2025-12-11 -> sort newer dates first)
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', model_id)
    date_sort = (0, 0, 0)
    if date_match:
        year, month, day = date_match.groups()
        # Negate to sort descending (newer dates first)
        date_sort = (-int(year), -int(month), -int(day))

    return (tier, date_sort, model_id_lower)


def fetch_models_from_provider(provider: str, api_key: str = "") -> List[Dict]:
    """Fetch available models from API provider"""
    models = []

    try:
        if provider == "OPENROUTER":
            # OpenRouter public API - no auth required for model list
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                for model in data.get("data", []):
                    models.append({
                        "id": model.get("id", ""),
                        "name": model.get("name", model.get("id", "")),
                        "context_length": model.get("context_length", "N/A"),
                        "pricing": model.get("pricing", {})
                    })

        elif provider == "OPENAI" and api_key:
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                for model in data.get("data", []):
                    model_id = model.get("id", "")
                    # Filter to show chat/completion models (exclude embeddings, whisper, tts, dall-e, etc.)
                    exclude_patterns = ["embedding", "whisper", "tts", "dall-e", "davinci", "babbage", "curie", "ada", "moderation"]
                    if not any(x in model_id.lower() for x in exclude_patterns):
                        models.append({
                            "id": model_id,
                            "name": model_id,
                            "context_length": "N/A",
                            "pricing": {}
                        })

        elif provider == "GROQ" and api_key:
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                for model in data.get("data", []):
                    models.append({
                        "id": model.get("id", ""),
                        "name": model.get("id", ""),
                        "context_length": model.get("context_window", "N/A"),
                        "pricing": {}
                    })

    except Exception as e:
        st.error(f"Error fetching models: {e}")

    # Sort models from newest to oldest
    models.sort(key=lambda m: _get_model_sort_key(m["id"]))

    return models


def update_models_from_provider():
    """Task Model Assignments - Assign specific API provider and model to each task"""
    st.markdown("### Model Assignments")
    st.caption("Assign a specific API Provider and Model to each task. If not assigned, the global sidebar selection will be used.")

    # Get current assignments
    current_assignments = get_all_task_model_assignments()

    # Get available API providers
    api_providers = get_api_providers_for_dropdown()
    provider_names = [p["key_name"].replace("_API_KEY", "") for p in api_providers]
    provider_display_names = [p["display_name"] for p in api_providers]

    # Load API keys to check which providers are configured
    api_keys = load_api_keys()

    # Track changes for batch save
    if 'task_assignment_changes' not in st.session_state:
        st.session_state['task_assignment_changes'] = {}

    st.markdown("---")

    # Header row
    hcol1, hcol2, hcol3 = st.columns([2, 2, 3])
    with hcol1:
        st.markdown("**Task**")
    with hcol2:
        st.markdown("**API Provider**")
    with hcol3:
        st.markdown("**Model**")

    # Display each task with dropdowns
    for task in AVAILABLE_TASKS:
        task_id = task["task_id"]
        task_name = task["task_name"]
        task_icon = task["icon"]

        # Get current assignment for this task
        current = current_assignments.get(task_id, {})
        current_provider = current.get("api_provider", "")
        current_model = current.get("model_name", "")

        col1, col2, col3 = st.columns([2, 2, 3])

        with col1:
            st.markdown(f"**{task_icon} {task_name}**")

        with col2:
            # API Provider dropdown
            try:
                default_provider_idx = provider_names.index(current_provider) if current_provider else 0
            except ValueError:
                default_provider_idx = 0

            # Add a "Use Global" option at the beginning
            provider_options = ["(Use Global)"] + provider_display_names
            selected_provider_idx = st.selectbox(
                f"Provider for {task_name}",
                range(len(provider_options)),
                format_func=lambda x: provider_options[x],
                index=0 if not current_provider else default_provider_idx + 1,
                key=f"provider_{task_id}",
                label_visibility="collapsed"
            )

            # Map back to provider key
            if selected_provider_idx == 0:
                selected_provider_key = ""  # Use Global
            else:
                selected_provider_key = provider_names[selected_provider_idx - 1]

        with col3:
            # Model dropdown - depends on selected provider
            if selected_provider_key:
                # Get enabled models for this provider
                provider_models = get_enabled_models_by_provider(selected_provider_key)
                model_names = [m["name"] for m in provider_models]

                if model_names:
                    try:
                        default_model_idx = model_names.index(current_model) if current_model in model_names else 0
                    except ValueError:
                        default_model_idx = 0

                    selected_model_idx = st.selectbox(
                        f"Model for {task_name}",
                        range(len(model_names)),
                        format_func=lambda x: model_names[x],
                        index=default_model_idx,
                        key=f"model_{task_id}",
                        label_visibility="collapsed"
                    )
                    selected_model = model_names[selected_model_idx]
                else:
                    st.caption("No models available")
                    selected_model = ""
            else:
                st.caption("Using global selection")
                selected_model = ""

        # Track changes
        if selected_provider_key:
            st.session_state['task_assignment_changes'][task_id] = {
                "task_name": task_name,
                "api_provider": selected_provider_key,
                "model_name": selected_model
            }
        elif task_id in st.session_state['task_assignment_changes']:
            # Mark for removal if switched to "Use Global"
            st.session_state['task_assignment_changes'][task_id] = None

    st.markdown("---")

    # Save button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Save Assignments", type="primary", use_container_width=True):
            saved = 0
            removed = 0
            for task_id, assignment in st.session_state['task_assignment_changes'].items():
                if assignment is None:
                    # Remove assignment (use global)
                    from settings.api_database import delete_task_model_assignment
                    if delete_task_model_assignment(task_id):
                        removed += 1
                elif assignment.get("api_provider") and assignment.get("model_name"):
                    if set_task_model_assignment(
                        task_id,
                        assignment["task_name"],
                        assignment["api_provider"],
                        assignment["model_name"]
                    ):
                        saved += 1

            if saved > 0 or removed > 0:
                st.success(f"Saved {saved} assignment(s), removed {removed} assignment(s)!")
                st.session_state['task_assignment_changes'] = {}
                st.rerun()
            else:
                st.info("No changes to save")

    with col2:
        st.caption("Tasks without an assignment will use the global model selected in the sidebar.")


def manage_prompt_templates():
    """Manage Prompt Templates section"""
    st.markdown("### Prompt Templates")
    st.caption("Customize the AI prompts used for generating CP, AP, FG, LG, LP, and assessments.")

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

    # Category icons
    category_icons = {
        "courseware": "📚",
        "course_proposal": "📄",
        "assessment": "✅",
    }

    # Category display names
    category_display_names = {
        "courseware": "Courseware (AP, FG, LG, LP)",
        "course_proposal": "Course Proposal (CP)",
        "assessment": "Assessment (SAQ, PP, CS)",
    }

    # Initialize edit state
    if 'editing_template_id' not in st.session_state:
        st.session_state['editing_template_id'] = None

    # Display templates by category
    for category, templates in sorted(templates_by_category.items()):
        icon = category_icons.get(category, "📋")
        display_name = category_display_names.get(category, category.title())

        with st.expander(f"{icon} {display_name} ({len(templates)} templates)", expanded=True):
            for template in templates:
                template_id = template["id"]
                is_editing = st.session_state['editing_template_id'] == template_id

                # Template header
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{template['display_name']}**")
                    if template['description']:
                        st.caption(template['description'])

                with col2:
                    if template['is_builtin']:
                        st.caption("Built-in")
                    else:
                        st.caption("Custom")

                with col3:
                    if is_editing:
                        if st.button("Cancel", key=f"cancel_{template_id}", use_container_width=True):
                            st.session_state['editing_template_id'] = None
                            st.rerun()
                    else:
                        if st.button("Edit", key=f"edit_{template_id}", use_container_width=True):
                            st.session_state['editing_template_id'] = template_id
                            st.rerun()

                # Edit form (shown when editing)
                if is_editing:
                    st.markdown("---")

                    # Display name
                    new_display_name = st.text_input(
                        "Display Name",
                        value=template['display_name'],
                        key=f"name_{template_id}"
                    )

                    # Description
                    new_description = st.text_input(
                        "Description",
                        value=template['description'] or "",
                        key=f"desc_{template_id}"
                    )

                    # Variables (comma-separated)
                    new_variables = st.text_input(
                        "Variables (comma-separated)",
                        value=template['variables'] or "",
                        key=f"vars_{template_id}",
                        help="Template variables like: schema, course_title, learning_outcomes"
                    )

                    # Content (large text area)
                    new_content = st.text_area(
                        "Prompt Content",
                        value=template['content'],
                        height=400,
                        key=f"content_{template_id}"
                    )

                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])

                    with btn_col1:
                        if st.button("💾 Save Changes", key=f"save_{template_id}", type="primary", use_container_width=True):
                            if update_prompt_template(
                                template_id,
                                content=new_content,
                                display_name=new_display_name,
                                description=new_description,
                                variables=new_variables
                            ):
                                st.success("Template saved!")
                                st.session_state['editing_template_id'] = None
                                st.rerun()
                            else:
                                st.error("Failed to save template")

                    with btn_col2:
                        if template['is_builtin']:
                            if st.button("🔄 Reset to Default", key=f"reset_{template_id}", use_container_width=True):
                                if reset_prompt_template_to_default(template_id):
                                    st.success("Template reset to default!")
                                    st.session_state['editing_template_id'] = None
                                    st.rerun()
                                else:
                                    st.error("Failed to reset template")
                        else:
                            if st.button("🗑️ Delete", key=f"delete_{template_id}", use_container_width=True):
                                if delete_prompt_template(template_id):
                                    st.success("Template deleted!")
                                    st.session_state['editing_template_id'] = None
                                    st.rerun()
                                else:
                                    st.error("Failed to delete template")

                    st.markdown("---")

                else:
                    # Show preview when not editing
                    preview_length = 150
                    content_preview = template['content'][:preview_length]
                    if len(template['content']) > preview_length:
                        content_preview += "..."
                    st.code(content_preview, language="markdown")

    st.markdown("---")

    # Add new template section
    with st.expander("➕ Add New Prompt Template", expanded=False):
        st.markdown("Create a custom prompt template")

        new_category = st.selectbox(
            "Category",
            options=["courseware", "course_proposal", "assessment"],
            format_func=lambda x: category_display_names.get(x, x.title()),
            key="new_template_category"
        )

        new_name = st.text_input(
            "Template Name (lowercase, no spaces)",
            placeholder="e.g., custom_generation",
            key="new_template_name"
        )

        new_display = st.text_input(
            "Display Name",
            placeholder="e.g., Custom Generation",
            key="new_template_display"
        )

        new_desc = st.text_input(
            "Description",
            placeholder="Brief description of what this template does",
            key="new_template_desc"
        )

        new_vars = st.text_input(
            "Variables (comma-separated)",
            placeholder="e.g., schema, course_title",
            key="new_template_vars"
        )

        new_template_content = st.text_area(
            "Prompt Content",
            height=200,
            placeholder="Enter your prompt template here...",
            key="new_template_content"
        )

        if st.button("➕ Add Template", type="primary"):
            if not new_name or not new_display or not new_template_content:
                st.error("Name, Display Name, and Content are required")
            elif not new_name.replace("_", "").isalnum():
                st.error("Template name must be alphanumeric with underscores only")
            else:
                if add_prompt_template(
                    category=new_category,
                    name=new_name.lower().replace(" ", "_"),
                    display_name=new_display,
                    content=new_template_content,
                    description=new_desc,
                    variables=new_vars
                ):
                    st.success(f"Template '{new_display}' added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add template. Name might already exist.")


if __name__ == "__main__":
    app()
