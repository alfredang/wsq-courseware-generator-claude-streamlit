"""
Settings Management Module

This module provides UI for managing LLM Models and API Keys.

Author: Wong Xin Ping
Date: 18 September 2025
"""

import streamlit as st
from typing import Dict, List, Any

# Import existing configurations
from settings.model_configs import MODEL_CHOICES
from settings.api_manager import load_api_keys, save_api_keys, load_custom_models, save_custom_models, add_custom_model, remove_custom_model, delete_api_key


def app():
    """Main settings application - API & LLM Models only"""
    st.title("⚙️ Settings")

    # Force refresh of models on settings page load
    if st.button("🔄 Refresh Models", help="Click to refresh the model list if custom models aren't showing"):
        # Clear relevant session state
        if 'custom_models' in st.session_state:
            del st.session_state['custom_models']
        if 'api_keys' in st.session_state:
            del st.session_state['api_keys']
        st.rerun()

    # API & LLM Models section
    st.subheader("🤖 API & LLM Models")
    manage_llm_settings()


def llm_settings_app():
    """API & LLM Models page"""
    st.title("🤖 API & LLM Models")
    manage_llm_settings()


def manage_llm_settings():
    """Manage LLM Models and API Keys"""

    # Create sub-tabs for API Keys and Custom Models
    api_tab, models_tab = st.tabs(["🔑 API Keys", "🤖 Custom Models"])

    with api_tab:
        manage_api_keys()

    with models_tab:
        manage_custom_models()


def manage_api_keys():
    """Manage API Keys section"""
    st.subheader("Existing API Keys")

    # Load current API keys
    current_keys = load_api_keys()

    # Define the API keys to display
    api_key_names = [
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY"
    ]

    # Store edited values
    edited_keys = {}

    # Display each API key with input field and delete button
    for key_name in api_key_names:
        col1, col2, col3 = st.columns([2, 4, 1])

        with col1:
            st.markdown(f"**{key_name}**")

        with col2:
            edited_keys[key_name] = st.text_input(
                key_name,
                value=current_keys.get(key_name, ""),
                type="password",
                label_visibility="collapsed",
                key=f"api_key_{key_name}"
            )

        with col3:
            if st.button("", key=f"delete_{key_name}", icon=":material/delete:"):
                current_keys[key_name] = ""
                if save_api_keys(current_keys):
                    st.rerun()

    st.markdown("")

    # Save All Changes button
    if st.button("Save All Changes", type="primary", icon=":material/save:"):
        for key_name in api_key_names:
            current_keys[key_name] = edited_keys.get(key_name, "")
        if save_api_keys(current_keys):
            st.success("API Keys saved successfully!")
            st.rerun()
        else:
            st.error("Error saving API Keys. Please try again.")


def quick_add_openrouter_model(name: str, model_id: str, temperature: float = 0.2):
    """Quick add an OpenRouter model with sensible defaults"""
    success = add_custom_model(
        name=name,
        provider="OpenAIChatCompletionClient",
        model_id=model_id,
        base_url="https://openrouter.ai/api/v1",
        temperature=temperature,
        api_provider="OPENROUTER",
        custom_api_key=""
    )

    if success:
        st.success(f"✅ Model '{name}' added successfully!")
        # Clear cache to reload models
        if 'custom_models' in st.session_state:
            del st.session_state['custom_models']
        st.rerun()
    else:
        st.error(f"❌ Failed to add model '{name}'")


def manage_custom_models():
    """Manage Custom Models section"""
    st.subheader("Add OpenRouter Models")

    # Display current models
    from settings.api_manager import get_all_available_models
    all_models = get_all_available_models()
    custom_models = load_custom_models()

    # Show all available models
    st.write("### 📚 Your Models")
    model_df_data = []
    for model_name, config in all_models.items():
        is_custom = any(m["name"] == model_name for m in custom_models)
        model_info = {
            "Model": model_name,
            "Type": "Custom" if is_custom else "Built-in",
            "OpenRouter ID": config["config"].get("model", "N/A"),
            "Temperature": config["config"].get("temperature", "N/A")
        }
        model_df_data.append(model_info)

    st.dataframe(model_df_data, use_container_width=True)

    st.markdown("---")

    # Quick add from dropdown
    st.write("### 🚀 Quick Add Popular Models")

    # Popular model options with their OpenRouter IDs
    popular_models = {
        "GPT-4o": "openai/gpt-4o",
        "GPT-4o Mini": "openai/gpt-4o-mini",
        "GPT-4 Turbo": "openai/gpt-4-turbo",
        "Claude 3.5 Sonnet": "anthropic/claude-3.5-sonnet",
        "Claude 3 Opus": "anthropic/claude-3-opus",
        "Claude 3 Haiku": "anthropic/claude-3-haiku",
        "Gemini 2.0 Flash": "google/gemini-2.0-flash-exp",
        "Gemini Pro 1.5": "google/gemini-pro-1.5",
        "Gemini Flash 1.5": "google/gemini-flash-1.5",
        "DeepSeek Chat": "deepseek/deepseek-chat",
        "DeepSeek Coder": "deepseek/deepseek-coder",
        "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct",
        "Llama 3.1 405B": "meta-llama/llama-3.1-405b-instruct",
        "Mistral Large": "mistralai/mistral-large",
        "Mixtral 8x22B": "mistralai/mixtral-8x22b-instruct"
    }

    with st.form("quick_add_model"):
        col1, col2 = st.columns([3, 1])

        with col1:
            selected_model = st.selectbox(
                "Select a Model",
                options=list(popular_models.keys()),
                help="Choose from popular OpenRouter models"
            )

        with col2:
            quick_temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.2,
                step=0.1,
                key="quick_temp"
            )

        quick_submitted = st.form_submit_button("➕ Add Selected Model", type="primary")

        if quick_submitted:
            model_id = popular_models[selected_model]
            st.info(f"🔄 Adding {selected_model}...")
            success = add_custom_model(
                name=selected_model,
                provider="OpenAIChatCompletionClient",
                model_id=model_id,
                base_url="https://openrouter.ai/api/v1",
                temperature=quick_temperature,
                api_provider="OPENROUTER",
                custom_api_key=""
            )

            if success:
                st.success(f"✅ Model '{selected_model}' added successfully!")
                if 'custom_models' in st.session_state:
                    del st.session_state['custom_models']
                st.rerun()
            else:
                st.error(f"❌ Failed to add model '{selected_model}'")

    st.markdown("---")

    # Add custom model manually
    st.write("### ➕ Add Custom Model (Manual)")

    # Show examples
    with st.expander("📝 Popular OpenRouter Model IDs", expanded=False):
        st.markdown("""
        **OpenAI:**
        - `openai/gpt-4o` - GPT-4o (latest)
        - `openai/gpt-4o-mini` - GPT-4o Mini
        - `openai/gpt-4-turbo` - GPT-4 Turbo
        - `openai/gpt-3.5-turbo` - GPT-3.5 Turbo

        **Anthropic:**
        - `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet (latest)
        - `anthropic/claude-3-opus` - Claude 3 Opus
        - `anthropic/claude-3-haiku` - Claude 3 Haiku

        **Google:**
        - `google/gemini-2.0-flash-exp` - Gemini 2.0 Flash
        - `google/gemini-pro-1.5` - Gemini Pro 1.5
        - `google/gemini-flash-1.5` - Gemini Flash 1.5

        **Meta:**
        - `meta-llama/llama-3.3-70b-instruct` - Llama 3.3 70B
        - `meta-llama/llama-3.1-405b-instruct` - Llama 3.1 405B

        **DeepSeek:**
        - `deepseek/deepseek-chat` - DeepSeek Chat
        - `deepseek/deepseek-coder` - DeepSeek Coder

        **Mistral:**
        - `mistralai/mistral-large` - Mistral Large
        - `mistralai/mixtral-8x22b-instruct` - Mixtral 8x22B

        💡 **Tip:** Most model IDs use latest version by default. See full list at [openrouter.ai/models](https://openrouter.ai/models)
        """)

    with st.form("add_custom_model"):
        col1, col2 = st.columns(2)

        with col1:
            model_name = st.text_input(
                "Model Display Name *",
                placeholder="e.g., GPT-4o-Custom",
                help="Friendly name shown in dropdowns"
            )
            model_id = st.text_input(
                "OpenRouter Model ID *",
                placeholder="e.g., openai/gpt-4o",
                help="Get from openrouter.ai/models"
            )

        with col2:
            temperature = st.slider("Temperature", 0.0, 2.0, 0.2, 0.1)

        # Always use OpenRouter
        provider = "OpenAIChatCompletionClient"
        base_url = "https://openrouter.ai/api/v1"
        api_provider = "OPENROUTER"
        custom_api_key = ""

        submitted = st.form_submit_button("➕ Add Model", type="primary")

        if submitted:
            if not model_name or not model_id:
                st.error("❌ Please fill in required fields: Model Display Name and Model ID")
            elif "/" not in model_id:
                st.error("❌ Invalid model ID format. Must be in format: provider/model-name (e.g., openai/gpt-4o)")
            elif model_id.count("/") > 1:
                st.error("❌ Invalid model ID format. Only one '/' allowed (e.g., openai/gpt-4o)")
            elif len(model_id.split("/")[0]) < 2 or len(model_id.split("/")[1]) < 2:
                st.error("❌ Invalid model ID. Provider and model name must each be at least 2 characters")
            else:
                st.info(f"🔄 Adding model '{model_name}'...")
                success = add_custom_model(
                    name=model_name,
                    provider=provider,
                    model_id=model_id,
                    base_url=base_url,
                    temperature=temperature,
                    api_provider=api_provider,
                    custom_api_key=custom_api_key
                )

                if success:
                    st.success(f"✅ Model '{model_name}' added successfully!")
                    # Clear session state to force refresh of models
                    if 'custom_models' in st.session_state:
                        del st.session_state['custom_models']
                    st.rerun()
                else:
                    st.error("❌ Failed to add model. Please try again.")

    # Remove custom models
    if custom_models:
        st.subheader("Remove Custom Models")
        for model in custom_models:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{model['name']}** - {model['config']['model']}")
            with col2:
                if st.button(f"🗑️ Remove", key=f"remove_{model['name']}"):
                    if remove_custom_model(model['name']):
                        st.success(f"✅ Model '{model['name']}' removed!")
                        # Clear session state to force refresh of models
                        if 'custom_models' in st.session_state:
                            del st.session_state['custom_models']
                        st.rerun()
                    else:
                        st.error("❌ Error removing model")


if __name__ == "__main__":
    app()
