"""
Dynamic API Key and Model Management

This module handles dynamic storage and retrieval of API keys and LLM models.
- API keys are loaded from .streamlit/secrets.toml (or environment variables)
- All model configurations (built-in + custom) are stored in SQLite database

Author: Wong Xin Ping
Updated: 26 January 2026
"""

import streamlit as st
import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import SQLite database operations
from settings.api_database import (
    get_all_models as db_get_all_models,
    get_all_custom_models as db_get_all_custom_models,
    get_builtin_models as db_get_builtin_models,
    add_custom_model as db_add_custom_model,
    delete_custom_model as db_delete_custom_model,
    model_exists as db_model_exists,
    migrate_from_json,
    migrate_from_old_schema,
    init_database
)

# Load environment variables from .env file
load_dotenv()

# Legacy JSON file paths (for migration)
LEGACY_CUSTOM_MODELS_FILE = "settings/config/custom_models.json"


def _get_secret(key: str, default: str = "") -> str:
    """Safely get a secret from st.secrets or environment variables"""
    # First try environment variables (from .env file)
    env_value = os.environ.get(key, "")
    if env_value:
        return env_value
    # Then try streamlit secrets
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def load_api_keys() -> Dict[str, str]:
    """Load API keys from secrets.toml or environment variables"""
    # Load from secrets.toml / environment variables only
    base_keys = {
        "OPENAI_API_KEY": _get_secret("OPENAI_API_KEY", ""),
        "DEEPSEEK_API_KEY": _get_secret("DEEPSEEK_API_KEY", ""),
        "GEMINI_API_KEY": _get_secret("GEMINI_API_KEY", ""),
        "OPENROUTER_API_KEY": _get_secret("OPENROUTER_API_KEY", ""),
        "GROQ_API_KEY": _get_secret("GROQ_API_KEY", ""),
        "GROK_API_KEY": _get_secret("GROK_API_KEY", "")
    }

    # Cache in session state for performance
    st.session_state['api_keys'] = base_keys
    return base_keys


def save_api_keys(keys: Dict[str, str]) -> bool:
    """
    Save API keys to session state.
    Note: Actual persistence should be done by editing .streamlit/secrets.toml
    """
    try:
        st.session_state['api_keys'] = keys
        return True
    except Exception as e:
        st.error(f"Error saving API keys: {e}")
        return False


def get_api_key(provider: str) -> str:
    """Get API key for specific provider"""
    keys = load_api_keys()
    key_name = f"{provider.upper()}_API_KEY"
    return keys.get(key_name, "")


def delete_api_key(key_name: str) -> bool:
    """Clear an API key from session state"""
    try:
        keys = load_api_keys()
        if key_name in keys:
            keys[key_name] = ""
            return save_api_keys(keys)
        return False
    except Exception as e:
        st.error(f"Error deleting API key: {e}")
        return False


def _migrate_json_to_sqlite():
    """Migrate custom models from JSON to SQLite (one-time migration)"""
    if os.path.exists(LEGACY_CUSTOM_MODELS_FILE):
        try:
            with open(LEGACY_CUSTOM_MODELS_FILE, 'r') as f:
                json_models = json.load(f)

            if json_models:
                migrated = migrate_from_json(json_models)
                if migrated > 0:
                    print(f"Migrated {migrated} custom models from JSON to SQLite")

                # Rename old file to indicate migration complete
                backup_file = LEGACY_CUSTOM_MODELS_FILE + ".migrated"
                os.rename(LEGACY_CUSTOM_MODELS_FILE, backup_file)
                print(f"Renamed {LEGACY_CUSTOM_MODELS_FILE} to {backup_file}")
        except Exception as e:
            print(f"Error during migration: {e}")


def load_custom_models() -> List[Dict[str, Any]]:
    """Load custom (non-built-in) LLM models from SQLite database"""
    # Check for and perform migration if needed
    _migrate_json_to_sqlite()

    # Load from SQLite
    models = db_get_all_custom_models()

    # Cache in session state
    st.session_state['custom_models'] = models
    return models


def load_builtin_models() -> List[Dict[str, Any]]:
    """Load built-in LLM models from SQLite database"""
    return db_get_builtin_models()


def save_custom_models(models: List[Dict[str, Any]]) -> bool:
    """
    Save custom models - now handled by individual add/remove operations.
    This function is kept for backward compatibility.
    """
    st.session_state['custom_models'] = models
    return True


def add_custom_model(
    name: str,
    provider: str,
    model_id: str,
    base_url: str = "",
    temperature: float = 0.2,
    api_provider: str = "",
    custom_api_key: str = ""
) -> bool:
    """Add a new custom model to SQLite database"""
    # Check if model already exists
    if db_model_exists(name):
        st.error(f"Model Display Name '{name}' already exists!")
        st.error("Please use a different name to distinguish between models.")
        return False

    # Add to database
    success = db_add_custom_model(
        name=name,
        model_id=model_id,
        provider=provider,
        base_url=base_url if base_url else "https://openrouter.ai/api/v1",
        temperature=temperature,
        api_provider=api_provider if api_provider else "OPENROUTER"
    )

    if success:
        # Clear session state cache to force reload
        if 'custom_models' in st.session_state:
            del st.session_state['custom_models']
        if 'all_models' in st.session_state:
            del st.session_state['all_models']

    return success


def remove_custom_model(name: str) -> bool:
    """Remove a custom model from SQLite database"""
    success = db_delete_custom_model(name)

    if success:
        # Clear session state cache to force reload
        if 'custom_models' in st.session_state:
            del st.session_state['custom_models']
        if 'all_models' in st.session_state:
            del st.session_state['all_models']

    return success


def get_all_available_models() -> Dict[str, Dict[str, Any]]:
    """Get all available models (built-in + custom) with current API keys from SQLite"""
    # Get current API keys
    current_keys = load_api_keys()

    # Get all models from SQLite database
    all_models = db_get_all_models(include_builtin=True)

    updated_models = {}
    for model in all_models:
        # Resolve API key based on api_provider
        api_provider = model.get("api_provider", "OPENROUTER")
        resolved_key = current_keys.get(f"{api_provider}_API_KEY", "")

        # Create model config with resolved API key
        model_with_key = {
            "name": model["name"],
            "provider": model["provider"],
            "config": {
                "model": model["config"]["model"],
                "temperature": model["config"]["temperature"],
                "base_url": model["config"].get("base_url", "https://openrouter.ai/api/v1"),
                "api_key": resolved_key
            },
            "is_builtin": model.get("is_builtin", False)
        }
        updated_models[model["name"]] = model_with_key

    return updated_models


def initialize_api_system():
    """Initialize the API system on app startup"""
    # Initialize SQLite database (includes seeding built-in models)
    init_database()

    # Migrate from old schema if needed
    migrate_from_old_schema()

    # Check for JSON migration
    _migrate_json_to_sqlite()

    # Load API keys into session state
    load_api_keys()
