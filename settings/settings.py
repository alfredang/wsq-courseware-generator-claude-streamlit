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
    get_default_model,
    set_default_model
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
    col1, col2, col3 = st.columns(3)
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
        if st.button("🔄 Update Models", use_container_width=True,
                     type="primary" if st.session_state['llm_settings_view'] == 'update_models' else "secondary"):
            st.session_state['llm_settings_view'] = 'update_models'
            st.rerun()

    st.markdown("---")

    # Display based on current view
    if st.session_state['llm_settings_view'] == 'api_keys':
        manage_api_keys()
    elif st.session_state['llm_settings_view'] == 'all_models':
        display_all_models()
    elif st.session_state['llm_settings_view'] == 'update_models':
        update_models_from_provider()


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
            # Get current default model for this provider
            default_model = get_default_model(provider)

            with st.expander(f"{provider} ({len(models)} models)", expanded=(len(providers_to_show) == 1)):
                # Header row
                hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([3, 3, 1.5, 1, 1])
                with hcol1:
                    st.markdown("**Model**")
                with hcol2:
                    st.markdown("**ID**")
                with hcol3:
                    st.markdown("**Temp**")
                with hcol4:
                    st.markdown("**Selected**")
                with hcol5:
                    st.markdown("**Default**")

                # Model rows
                for idx, model in enumerate(models):
                    model_name = model["name"]
                    model_id = model["config"].get("model", "N/A")
                    temp = model["config"].get("temperature", 0.2)
                    is_enabled = model.get("is_enabled", True)
                    is_default = default_model == model_name

                    col1, col2, col3, col4, col5 = st.columns([3, 3, 1.5, 1, 1])

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
                    with col5:
                        # Default radio button
                        if st.button("◉" if is_default else "○", key=f"def_{provider}_{idx}", help="Set as default"):
                            if not is_default:
                                set_default_model(provider, model_name)
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
    """Update models by fetching from API providers"""
    st.caption("Fetch and add latest models from API providers")

    # Get available API providers
    api_providers = get_api_providers_for_dropdown()
    provider_options = {p["display_name"]: p for p in api_providers}

    # Provider selection
    selected_provider_name = st.selectbox(
        "Select API Provider",
        options=list(provider_options.keys()),
        index=0,
        help="Choose provider to fetch models from"
    )

    selected_provider = provider_options.get(selected_provider_name, {})
    provider_key = selected_provider.get("key_name", "OPENROUTER_API_KEY").replace("_API_KEY", "")
    base_url = selected_provider.get("base_url", "https://openrouter.ai/api/v1")

    # Get API key for this provider
    api_keys = load_api_keys()
    api_key = api_keys.get(f"{provider_key}_API_KEY", "")

    # Initialize session state for fetched models
    if 'fetched_models' not in st.session_state:
        st.session_state['fetched_models'] = []
    if 'fetched_provider' not in st.session_state:
        st.session_state['fetched_provider'] = ""
    if 'selected_models' not in st.session_state:
        st.session_state['selected_models'] = set()

    # Fetch models button
    fetch_clicked = st.button("🔍 Fetch Models", type="primary")

    if fetch_clicked:
        if provider_key not in ["OPENROUTER"] and not api_key:
            st.warning(f"API key required for {provider_key}. Add it in the API Keys tab.")
        else:
            with st.spinner(f"Fetching models from {provider_key}..."):
                models = fetch_models_from_provider(provider_key, api_key)
                if models:
                    st.session_state['fetched_models'] = models
                    st.session_state['fetched_provider'] = provider_key
                    # Reset preselection and selection for new fetch
                    st.session_state['selected_models'] = set()
                    if 'existing_preselected' in st.session_state:
                        del st.session_state['existing_preselected']
                    st.success(f"Found {len(models)} models")
                    st.rerun()  # Rerun to apply preselection
                else:
                    st.warning("No models found or API not accessible")
                    st.session_state['fetched_models'] = []

    # Display fetched models with checkboxes
    if st.session_state['fetched_models'] and st.session_state['fetched_provider'] == provider_key:
        models = st.session_state['fetched_models']

        st.markdown("---")
        st.caption(f"{len(models)} models available from {provider_key}")

        # Search/filter
        search = st.text_input("🔍 Filter models", placeholder="Type to filter...")

        # Filter models
        if search:
            filtered_models = [m for m in models if search.lower() in m["id"].lower() or search.lower() in m["name"].lower()]
        else:
            filtered_models = models

        # Get existing model IDs to check for duplicates
        existing_models = get_all_available_models()
        existing_ids = {config["config"].get("model", "") for config in existing_models.values()}

        # Auto-select existing models on first load (so they appear checked)
        if 'existing_preselected' not in st.session_state:
            for m in filtered_models:
                if m["id"] in existing_ids:
                    st.session_state['selected_models'].add(m["id"])
            st.session_state['existing_preselected'] = True

        # Select all / Deselect all / Add Selected
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Select All", use_container_width=True):
                st.session_state['selected_models'] = {m["id"] for m in filtered_models}
                st.rerun()
        with col2:
            if st.button("Deselect All", use_container_width=True):
                st.session_state['selected_models'] = set()
                st.rerun()
        with col3:
            # Count new models to add (not already in database)
            new_models_to_add = [m for m in filtered_models
                                 if m["id"] in st.session_state['selected_models']
                                 and m["id"] not in existing_ids]
            add_count = len(new_models_to_add)

            if st.button(f"➕ Add {add_count} Selected", type="primary", use_container_width=True, disabled=(add_count == 0)):
                added = 0
                for model in new_models_to_add:
                    model_id = model["id"]
                    # Create display name from model ID
                    display_name = model_id.replace("/", " - ").replace("-", " ").title()

                    success = add_custom_model(
                        name=display_name,
                        provider=provider_key,
                        model_id=model_id,
                        base_url=base_url,
                        temperature=0.2,
                        api_provider=provider_key
                    )
                    if success:
                        added += 1

                if added > 0:
                    st.success(f"Added {added} models!")
                    # Clear caches
                    if 'custom_models' in st.session_state:
                        del st.session_state['custom_models']
                    if 'all_models' in st.session_state:
                        del st.session_state['all_models']
                    st.rerun()
                else:
                    st.warning("No new models were added")

        # Display models in a scrollable container
        st.markdown(f"**Showing {len(filtered_models)} models:**")

        # Create checkboxes for each model
        for model in filtered_models[:100]:  # Limit to 100 for performance
            model_id = model["id"]
            is_existing = model_id in existing_ids

            col1, col2 = st.columns([1, 5])
            with col1:
                checked = st.checkbox(
                    "",
                    value=model_id in st.session_state['selected_models'],
                    key=f"chk_{model_id}"
                )
                if checked and model_id not in st.session_state['selected_models']:
                    st.session_state['selected_models'].add(model_id)
                elif not checked and model_id in st.session_state['selected_models']:
                    st.session_state['selected_models'].discard(model_id)

            with col2:
                st.markdown(f"<span style='color:#ffffff; font-size:1.1rem;'>{model_id}</span>", unsafe_allow_html=True)

        if len(filtered_models) > 100:
            st.caption(f"Showing first 100 of {len(filtered_models)} models. Use filter to narrow down.")


if __name__ == "__main__":
    app()
