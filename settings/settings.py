"""
Settings Management Module

This module provides UI for managing LLM Models and API Keys.
All models (built-in + custom) are stored in SQLite database.

Author: Wong Xin Ping
Date: 18 September 2025
Updated: 26 January 2026
"""

import streamlit as st
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
    get_all_available_models
)


def app():
    """Main settings application - API & LLM Models only"""
    st.title("Settings")

    # Force refresh of models on settings page load
    if st.button("Refresh Models", help="Click to refresh the model list"):
        # Clear relevant session state
        if 'custom_models' in st.session_state:
            del st.session_state['custom_models']
        if 'api_keys' in st.session_state:
            del st.session_state['api_keys']
        if 'all_models' in st.session_state:
            del st.session_state['all_models']
        st.rerun()

    # API & LLM Models section
    st.subheader("API & LLM Models")
    manage_llm_settings()


def llm_settings_app():
    """API & LLM Models page"""
    st.title("API & LLM Models")
    manage_llm_settings()


def manage_llm_settings():
    """Manage LLM Models and API Keys"""

    # Create sub-tabs for API Keys and Models
    api_tab, models_tab, custom_tab = st.tabs(["API Keys", "All Models", "Add Custom Model"])

    with api_tab:
        manage_api_keys()

    with models_tab:
        display_all_models()

    with custom_tab:
        manage_custom_models()


def manage_api_keys():
    """Manage API Keys section"""
    st.subheader("Existing API Keys")

    # Info about where API keys are stored
    st.info(
        "API keys are loaded from `.streamlit/secrets.toml` or environment variables. "
        "To add or modify keys, edit the secrets.toml file directly."
    )

    # Load current API keys
    current_keys = load_api_keys()

    # Define the API keys to display
    api_key_names = [
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY"
    ]

    # Display each API key (read-only view showing if configured)
    for key_name in api_key_names:
        col1, col2 = st.columns([2, 4])

        with col1:
            st.markdown(f"**{key_name}**")

        with col2:
            key_value = current_keys.get(key_name, "")
            if key_value:
                # Show masked key
                masked = key_value[:8] + "..." + key_value[-4:] if len(key_value) > 12 else "****"
                st.success(f"Configured ({masked})")
            else:
                st.warning("Not configured")

    st.markdown("")

    # Show help for configuring secrets
    with st.expander("How to configure API keys"):
        st.markdown("""
        **Edit `.streamlit/secrets.toml`:**
        ```toml
        OPENAI_API_KEY = "sk-your-key-here"
        OPENROUTER_API_KEY = "sk-or-your-key-here"
        DEEPSEEK_API_KEY = "sk-your-key-here"
        GEMINI_API_KEY = "your-key-here"
        ```

        **For Streamlit Cloud deployment:**
        Add secrets in the Streamlit Cloud dashboard under Settings > Secrets.

        **Recommended:** Use OpenRouter API key for access to multiple models through a single key.
        """)


def display_all_models():
    """Display all available models (built-in + custom)"""
    st.subheader("Available LLM Models")

    all_models = get_all_available_models()
    custom_models = load_custom_models()
    custom_names = {m["name"] for m in custom_models}

    # Separate built-in and custom models
    builtin_data = []
    custom_data = []

    for model_name, config in all_models.items():
        model_info = {
            "Model": model_name,
            "OpenRouter ID": config["config"].get("model", "N/A"),
            "Temperature": config["config"].get("temperature", "N/A")
        }

        if model_name in custom_names or config.get("is_builtin") is False:
            custom_data.append(model_info)
        else:
            builtin_data.append(model_info)

    # Display built-in models
    st.write("### Built-in Models")
    st.caption(f"{len(builtin_data)} models available via OpenRouter")
    if builtin_data:
        st.dataframe(builtin_data, use_container_width=True, hide_index=True)

    # Display custom models
    if custom_data:
        st.write("### Custom Models")
        st.caption(f"{len(custom_data)} custom models added")
        st.dataframe(custom_data, use_container_width=True, hide_index=True)

        # Remove custom models section
        st.write("#### Remove Custom Models")
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


def manage_custom_models():
    """Manage Custom Models section"""
    st.subheader("Add Custom Model")

    st.info("Add any model available on OpenRouter. All models use your OpenRouter API key.")

    # Add custom model form
    with st.form("add_custom_model"):
        col1, col2 = st.columns(2)

        with col1:
            model_name = st.text_input(
                "Model Display Name *",
                placeholder="e.g., My-Custom-GPT",
                help="Friendly name shown in model selection dropdown"
            )
            model_id = st.text_input(
                "OpenRouter Model ID *",
                placeholder="e.g., openai/gpt-4o",
                help="Get model IDs from openrouter.ai/models"
            )

        with col2:
            temperature = st.slider("Temperature", 0.0, 2.0, 0.2, 0.1)
            st.caption("Lower = more focused, Higher = more creative")

        # Always use OpenRouter
        provider = "OpenAIChatCompletionClient"
        base_url = "https://openrouter.ai/api/v1"
        api_provider = "OPENROUTER"

        submitted = st.form_submit_button("Add Model", type="primary")

        if submitted:
            if not model_name or not model_id:
                st.error("Please fill in required fields: Model Display Name and Model ID")
            elif "/" not in model_id:
                st.error("Invalid model ID format. Must be in format: provider/model-name (e.g., openai/gpt-4o)")
            elif model_id.count("/") > 1:
                st.error("Invalid model ID format. Only one '/' allowed (e.g., openai/gpt-4o)")
            elif len(model_id.split("/")[0]) < 2 or len(model_id.split("/")[1]) < 2:
                st.error("Invalid model ID. Provider and model name must each be at least 2 characters")
            else:
                success = add_custom_model(
                    name=model_name,
                    provider=provider,
                    model_id=model_id,
                    base_url=base_url,
                    temperature=temperature,
                    api_provider=api_provider,
                    custom_api_key=""
                )

                if success:
                    st.success(f"Model '{model_name}' added successfully!")
                    if 'custom_models' in st.session_state:
                        del st.session_state['custom_models']
                    st.rerun()
                else:
                    st.error("Failed to add model. Name may already exist.")

    # Show popular model IDs for reference
    with st.expander("Popular OpenRouter Model IDs"):
        st.markdown("""
        **OpenAI:**
        - `openai/gpt-5` - GPT-5
        - `openai/gpt-4.1` - GPT-4.1
        - `openai/gpt-4o` - GPT-4o
        - `openai/o3` - OpenAI o3 (reasoning)

        **Anthropic:**
        - `anthropic/claude-opus-4.5` - Claude Opus 4.5
        - `anthropic/claude-sonnet-4.5` - Claude Sonnet 4.5
        - `anthropic/claude-sonnet-4` - Claude Sonnet 4

        **Google:**
        - `google/gemini-3-pro-preview` - Gemini 3 Pro
        - `google/gemini-2.5-flash` - Gemini 2.5 Flash

        **DeepSeek:**
        - `deepseek/deepseek-chat` - DeepSeek V3
        - `deepseek/deepseek-r1` - DeepSeek R1 (reasoning)

        **Qwen:**
        - `qwen/qwq-32b` - QwQ 32B (reasoning)
        - `qwen/qwen-2.5-72b-instruct` - Qwen 2.5 72B

        **Meta:**
        - `meta-llama/llama-3.3-70b-instruct` - Llama 3.3 70B

        See full list at [openrouter.ai/models](https://openrouter.ai/models)
        """)


if __name__ == "__main__":
    app()
