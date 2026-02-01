"""
Settings Module - Chainlit

Handles application settings:
- API key configuration
- Model selection
- Company selection

Author: Courseware Generator Team
Date: February 2026
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl
from chainlit.input_widget import TextInput, Select, Switch

# Import existing settings modules
try:
    from settings.api_manager import load_api_keys, save_api_keys, get_all_available_models
    from settings.api_database import get_all_models, set_task_model_assignment, get_task_model_assignment
    from company.company_manager import get_organizations
except ImportError as e:
    print(f"Warning: Could not import settings modules: {e}")


# API Providers
API_PROVIDERS = [
    ("OPENROUTER", "OpenRouter"),
    ("OPENAI", "OpenAI"),
    ("ANTHROPIC", "Anthropic"),
    ("GEMINI", "Google Gemini"),
    ("GROQ", "Groq"),
    ("GROK", "xAI Grok"),
    ("DEEPSEEK", "DeepSeek"),
]


async def on_start():
    """Called when Settings profile is selected."""
    cl.user_session.set("settings_state", "main")

    # Show main settings menu
    actions = [
        cl.Action(name="settings_api_keys", value="api_keys", label="Configure API Keys"),
        cl.Action(name="settings_models", value="models", label="Model Selection"),
        cl.Action(name="settings_company", value="company", label="Company Selection"),
    ]

    await cl.Message(
        content="**Settings Menu**\n\nWhat would you like to configure?",
        actions=actions
    ).send()


async def on_message(message: cl.Message):
    """Handle messages in Settings context."""
    content = message.content.lower()

    if any(kw in content for kw in ["api", "key", "keys"]):
        await show_api_keys()
    elif any(kw in content for kw in ["model", "models", "llm"]):
        await show_models()
    elif any(kw in content for kw in ["company", "organization"]):
        await show_company_selection()
    elif any(kw in content for kw in ["back", "menu", "home"]):
        await on_start()
    else:
        await cl.Message(
            content="Available settings:\n"
                    "- **API Keys** - Configure API provider keys\n"
                    "- **Models** - Select default LLM model\n"
                    "- **Company** - Switch company/organization\n\n"
                    "What would you like to configure?"
        ).send()


async def on_settings_update(settings_update):
    """Handle settings form updates."""
    try:
        for key, value in settings_update.items():
            if key.endswith("_API_KEY") and value:
                # Mask check - don't save masked values
                if not value.startswith("***"):
                    # Load current keys, update, and save
                    current_keys = load_api_keys()
                    current_keys[key] = value
                    save_api_keys(current_keys)
                    provider = key.replace("_API_KEY", "")
                    await cl.Message(content=f"Updated {provider} API key.").send()

            elif key == "default_model":
                # Save model selection
                cl.user_session.set("selected_model", value)
                await cl.Message(content=f"Default model set to: {value}").send()

            elif key == "selected_company":
                # Save company selection
                organizations = get_organizations()
                for org in organizations:
                    if org["name"] == value:
                        cl.user_session.set("selected_company", org)
                        await cl.Message(content=f"Switched to: {value}").send()
                        break

    except Exception as e:
        await cl.Message(content=f"Error saving settings: {e}").send()


async def show_api_keys():
    """Show API key configuration."""
    try:
        current_keys = load_api_keys()
    except:
        current_keys = {}

    settings = []

    for provider_key, provider_name in API_PROVIDERS:
        key_name = f"{provider_key}_API_KEY"
        current_value = current_keys.get(key_name, "")

        # Mask the key for display
        if current_value:
            masked = f"***{current_value[-4:]}" if len(current_value) > 4 else "****"
        else:
            masked = ""

        settings.append(
            TextInput(
                id=key_name,
                label=f"{provider_name} API Key",
                initial=masked,
                placeholder="Enter API key..."
            )
        )

    await cl.ChatSettings(settings).send()

    await cl.Message(
        content="**API Key Configuration**\n\n"
                "Enter your API keys above. Keys are stored securely.\n\n"
                "**Note:** Existing keys are masked. Enter a new value to update."
    ).send()


async def show_models():
    """Show model selection."""
    try:
        all_models = get_all_models(include_builtin=True)
        model_names = [m["name"] for m in all_models if m.get("is_enabled", True)]
    except:
        model_names = ["claude-sonnet-4", "gpt-4o", "deepseek-chat"]

    current_model = cl.user_session.get("selected_model", model_names[0] if model_names else "")

    settings = [
        Select(
            id="default_model",
            label="Default Model",
            values=model_names,
            initial_value=current_model
        )
    ]

    await cl.ChatSettings(settings).send()

    await cl.Message(
        content="**Model Selection**\n\n"
                "Choose the default LLM model for generation tasks.\n\n"
                f"**Current:** {current_model}"
    ).send()


async def show_company_selection():
    """Show company selection."""
    try:
        organizations = get_organizations()
        company_names = [org["name"] for org in organizations]
    except:
        company_names = ["Default Company"]

    current_company = cl.user_session.get("selected_company", {})
    current_name = current_company.get("name", company_names[0] if company_names else "")

    settings = [
        Select(
            id="selected_company",
            label="Company",
            values=company_names,
            initial_value=current_name
        )
    ]

    await cl.ChatSettings(settings).send()

    await cl.Message(
        content="**Company Selection**\n\n"
                "Select the company for branding and templates.\n\n"
                f"**Current:** {current_name}"
    ).send()


def get_masked_key(provider: str) -> str:
    """Get masked API key for display."""
    try:
        keys = load_api_keys()
        key = keys.get(f"{provider}_API_KEY", "")
        if key:
            return f"***{key[-4:]}" if len(key) > 4 else "****"
    except:
        pass
    return ""


def get_model_names() -> list:
    """Get list of available model names."""
    try:
        models = get_all_models(include_builtin=True)
        return [m["name"] for m in models if m.get("is_enabled", True)]
    except:
        return ["claude-sonnet-4", "gpt-4o", "deepseek-chat"]


def get_default_model() -> str:
    """Get current default model."""
    return cl.user_session.get("selected_model", "claude-sonnet-4")
