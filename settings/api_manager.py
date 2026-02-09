"""
Dynamic API Key and Model Management

This module handles dynamic storage and retrieval of API keys and LLM models.
- API keys are loaded from environment variables or secrets.toml
- All model configurations (built-in + custom) are stored in SQLite database

Author: Wong Xin Ping
Updated: February 2026
"""

import json
import os
from typing import Dict, Any, List, Optional
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
    init_database,
    refresh_builtin_models as db_refresh_builtin_models,
    refresh_builtin_api_keys as db_refresh_builtin_api_keys,
    # API key config functions
    get_all_api_key_configs as db_get_all_api_key_configs,
    get_api_key_config as db_get_api_key_config,
    add_api_key_config as db_add_api_key_config,
    delete_api_key_config as db_delete_api_key_config,
    update_api_key_configured_status as db_update_api_key_configured_status,
    api_key_config_exists as db_api_key_config_exists
)

# Load environment variables from .env file
load_dotenv()

# Legacy JSON file paths (for migration)
LEGACY_CUSTOM_MODELS_FILE = "settings/config/custom_models.json"

# Module-level cache (replaces st.session_state)
_cache: Dict[str, Any] = {}

def _get_secret(key: str, default: str = "") -> str:
    """Safely get a secret from environment variables"""
    return os.environ.get(key, default)


def load_api_keys() -> Dict[str, str]:
    """Load all API keys from secrets.toml or environment variables based on database config"""
    # Initialize database to ensure api_keys table exists
    init_database()

    # Get all configured API key names from database
    api_key_configs = db_get_all_api_key_configs()

    # Load each configured API key from secrets/env
    api_keys = {}
    for config in api_key_configs:
        key_name = config["key_name"]
        key_value = _get_secret(key_name, "")
        api_keys[key_name] = key_value

        # Update configured status in database
        db_update_api_key_configured_status(key_name, bool(key_value))

    # Cache for performance
    _cache['api_keys'] = api_keys
    return api_keys


def save_api_keys(keys: Dict[str, str]) -> bool:
    """
    Save API keys to cache.
    Note: Actual persistence should be done by editing secrets.toml or .env
    """
    try:
        _cache['api_keys'] = keys
        return True
    except Exception as e:
        print(f"Error saving API keys: {e}")
        return False


def get_api_key(provider: str) -> str:
    """Get API key for specific provider"""
    keys = load_api_keys()
    key_name = f"{provider.upper()}_API_KEY"
    return keys.get(key_name, "")


def delete_api_key(key_name: str) -> bool:
    """Clear an API key from cache"""
    try:
        keys = load_api_keys()
        if key_name in keys:
            keys[key_name] = ""
            return save_api_keys(keys)
        return False
    except Exception as e:
        print(f"Error deleting API key: {e}")
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

    # Cache
    _cache['custom_models'] = models
    return models


def load_builtin_models() -> List[Dict[str, Any]]:
    """Load built-in LLM models from SQLite database"""
    return db_get_builtin_models()


def save_custom_models(models: List[Dict[str, Any]]) -> bool:
    """
    Save custom models - now handled by individual add/remove operations.
    This function is kept for backward compatibility.
    """
    _cache['custom_models'] = models
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
        print(f"Model Display Name '{name}' already exists! Please use a different name.")
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
        # Clear cache to force reload
        _cache.pop('custom_models', None)
        _cache.pop('all_models', None)

    return success


def remove_custom_model(name: str) -> bool:
    """Remove a custom model from SQLite database"""
    success = db_delete_custom_model(name)

    if success:
        # Clear cache to force reload
        _cache.pop('custom_models', None)
        _cache.pop('all_models', None)

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
            "api_provider": api_provider,
            "is_builtin": model.get("is_builtin", False)
        }
        updated_models[model["name"]] = model_with_key

    return updated_models


def initialize_api_system():
    """Initialize the API system on app startup"""
    # Initialize SQLite database (includes seeding built-in models and API key configs)
    init_database()

    # Migrate from old schema if needed
    migrate_from_old_schema()

    # Check for JSON migration
    _migrate_json_to_sqlite()

    # Refresh built-in models and API keys (updates display names and adds new models)
    db_refresh_builtin_models()
    db_refresh_builtin_api_keys()

    # Load API keys into cache
    load_api_keys()


# ============ API Key Configuration Management ============

def get_all_api_key_configs() -> List[Dict[str, Any]]:
    """Get all API key configurations from database"""
    return db_get_all_api_key_configs()


def add_api_key_config(
    key_name: str,
    display_name: str,
    base_url: str = "",
    description: str = ""
) -> bool:
    """Add a new API key configuration"""
    # Ensure key_name is in correct format
    if not key_name.endswith("_API_KEY"):
        key_name = f"{key_name.upper()}_API_KEY"

    if db_api_key_config_exists(key_name):
        print(f"API key '{key_name}' already exists!")
        return False

    success = db_add_api_key_config(
        key_name=key_name,
        display_name=display_name,
        base_url=base_url,
        description=description
    )

    if success:
        # Clear cache to force reload
        _cache.pop('api_keys', None)

    return success


def remove_api_key_config(key_name: str) -> bool:
    """Remove an API key configuration (only custom ones)"""
    success = db_delete_api_key_config(key_name)

    if success:
        # Clear cache to force reload
        _cache.pop('api_keys', None)

    return success


def get_api_providers_for_dropdown() -> List[Dict[str, str]]:
    """Get list of API providers for dropdown selection in custom model form"""
    configs = db_get_all_api_key_configs()
    return [
        {
            "key_name": c["key_name"],
            "display_name": c["display_name"],
            "base_url": c["base_url"] or ""
        }
        for c in configs
    ]
