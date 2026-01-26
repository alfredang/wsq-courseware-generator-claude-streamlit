"""
API Configuration Database Module

This module provides SQLite-based storage for API configuration metadata.
Actual API key values are stored in .streamlit/secrets.toml for security.

SQLite stores:
- LLM model configurations (both built-in and custom)
- Provider settings (enabled status, base URLs)

Author: Claude Code
Date: 26 January 2026
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

# Database file location
DB_PATH = "settings/config/api_config.db"

# Database version for migrations
DB_VERSION = 2


def get_db_path() -> str:
    """Get the database file path, ensuring directory exists"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Models table (both built-in and custom)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL DEFAULT 'OpenAIChatCompletionClient',
                model_id TEXT NOT NULL,
                base_url TEXT DEFAULT 'https://openrouter.ai/api/v1',
                temperature REAL DEFAULT 0.2,
                api_provider TEXT DEFAULT 'OPENROUTER',
                is_builtin INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Provider settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT UNIQUE NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                base_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Database version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY
            )
        """)

        conn.commit()

    # Seed built-in models if not already present
    _seed_builtin_models()


# ============ Built-in Models Seed Data ============

BUILTIN_MODELS = [
    # === OpenAI Models ===
    {"name": "GPT-5", "model_id": "openai/gpt-5", "api_provider": "OPENROUTER", "sort_order": 1},
    {"name": "GPT-5-Mini", "model_id": "openai/gpt-5-mini", "api_provider": "OPENROUTER", "sort_order": 2},
    {"name": "GPT-4.1", "model_id": "openai/gpt-4.1", "api_provider": "OPENROUTER", "sort_order": 3},
    {"name": "GPT-4.1-Mini", "model_id": "openai/gpt-4.1-mini", "api_provider": "OPENROUTER", "sort_order": 4},
    {"name": "GPT-4.1-Nano", "model_id": "openai/gpt-4.1-nano", "api_provider": "OPENROUTER", "sort_order": 5},
    {"name": "GPT-4o", "model_id": "openai/gpt-4o", "api_provider": "OPENROUTER", "sort_order": 6},
    {"name": "GPT-4o-Mini", "model_id": "openai/gpt-4o-mini", "api_provider": "OPENROUTER", "sort_order": 7},
    {"name": "o3", "model_id": "openai/o3", "api_provider": "OPENROUTER", "sort_order": 8},
    {"name": "o3-Mini", "model_id": "openai/o3-mini", "api_provider": "OPENROUTER", "sort_order": 9},
    {"name": "o3-Pro", "model_id": "openai/o3-pro", "api_provider": "OPENROUTER", "sort_order": 10},
    {"name": "o4-Mini", "model_id": "openai/o4-mini", "api_provider": "OPENROUTER", "sort_order": 11},
    {"name": "o1", "model_id": "openai/o1", "api_provider": "OPENROUTER", "sort_order": 12},

    # === Anthropic Claude Models ===
    {"name": "Claude-Opus-4.5", "model_id": "anthropic/claude-opus-4.5", "api_provider": "OPENROUTER", "sort_order": 20},
    {"name": "Claude-Sonnet-4.5", "model_id": "anthropic/claude-sonnet-4.5", "api_provider": "OPENROUTER", "sort_order": 21},
    {"name": "Claude-Opus-4", "model_id": "anthropic/claude-opus-4", "api_provider": "OPENROUTER", "sort_order": 22},
    {"name": "Claude-Sonnet-4", "model_id": "anthropic/claude-sonnet-4", "api_provider": "OPENROUTER", "sort_order": 23},
    {"name": "Claude-Haiku-4.5", "model_id": "anthropic/claude-haiku-4.5", "api_provider": "OPENROUTER", "sort_order": 24},
    {"name": "Claude-3.5-Sonnet", "model_id": "anthropic/claude-3.5-sonnet", "api_provider": "OPENROUTER", "sort_order": 25},

    # === Google Gemini Models ===
    {"name": "Gemini-3-Pro", "model_id": "google/gemini-3-pro-preview", "api_provider": "OPENROUTER", "sort_order": 30},
    {"name": "Gemini-2.5-Pro", "model_id": "google/gemini-2.5-pro", "api_provider": "OPENROUTER", "sort_order": 31},
    {"name": "Gemini-2.5-Flash", "model_id": "google/gemini-2.5-flash", "api_provider": "OPENROUTER", "sort_order": 32},
    {"name": "Gemini-2.5-Flash-Lite", "model_id": "google/gemini-2.5-flash-lite", "api_provider": "OPENROUTER", "sort_order": 33},
    {"name": "Gemini-2.0-Flash", "model_id": "google/gemini-2.0-flash-exp", "api_provider": "OPENROUTER", "sort_order": 34},
    {"name": "Gemini-Pro-1.5", "model_id": "google/gemini-pro-1.5", "api_provider": "OPENROUTER", "sort_order": 35},

    # === DeepSeek Models ===
    {"name": "DeepSeek-V3", "model_id": "deepseek/deepseek-chat", "api_provider": "OPENROUTER", "sort_order": 40},
    {"name": "DeepSeek-R1", "model_id": "deepseek/deepseek-r1", "api_provider": "OPENROUTER", "sort_order": 41},
    {"name": "DeepSeek-R1-Distill-Qwen-32B", "model_id": "deepseek/deepseek-r1-distill-qwen-32b", "api_provider": "OPENROUTER", "sort_order": 42},

    # === Qwen Models ===
    {"name": "QwQ-32B", "model_id": "qwen/qwq-32b", "api_provider": "OPENROUTER", "sort_order": 50},
    {"name": "Qwen-2.5-72B-Instruct", "model_id": "qwen/qwen-2.5-72b-instruct", "api_provider": "OPENROUTER", "sort_order": 51},
    {"name": "Qwen-2.5-32B-Instruct", "model_id": "qwen/qwen-2.5-32b-instruct", "api_provider": "OPENROUTER", "sort_order": 52},
    {"name": "Qwen-2.5-Coder-32B", "model_id": "qwen/qwen-2.5-coder-32b-instruct", "api_provider": "OPENROUTER", "sort_order": 53},
    {"name": "Qwen3-VL-32B", "model_id": "qwen/qwen3-vl-32b", "api_provider": "OPENROUTER", "sort_order": 54},

    # === Meta Llama Models ===
    {"name": "Llama-3.3-70B", "model_id": "meta-llama/llama-3.3-70b-instruct", "api_provider": "OPENROUTER", "sort_order": 60},
    {"name": "Llama-3.1-405B", "model_id": "meta-llama/llama-3.1-405b-instruct", "api_provider": "OPENROUTER", "sort_order": 61},
    {"name": "Llama-3.1-70B", "model_id": "meta-llama/llama-3.1-70b-instruct", "api_provider": "OPENROUTER", "sort_order": 62},

    # === Mistral Models ===
    {"name": "Mistral-Large", "model_id": "mistralai/mistral-large", "api_provider": "OPENROUTER", "sort_order": 70},
    {"name": "Mixtral-8x22B", "model_id": "mistralai/mixtral-8x22b-instruct", "api_provider": "OPENROUTER", "sort_order": 71},
    {"name": "Codestral", "model_id": "mistralai/codestral", "api_provider": "OPENROUTER", "sort_order": 72},
]


def _seed_builtin_models():
    """Seed the database with built-in models if they don't exist"""
    with get_connection() as conn:
        cursor = conn.cursor()

        for model in BUILTIN_MODELS:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO llm_models
                    (name, provider, model_id, base_url, temperature, api_provider, is_builtin, sort_order)
                    VALUES (?, 'OpenAIChatCompletionClient', ?, 'https://openrouter.ai/api/v1', 0.2, ?, 1, ?)
                """, (model["name"], model["model_id"], model["api_provider"], model["sort_order"]))
            except Exception as e:
                print(f"Error seeding model {model['name']}: {e}")

        conn.commit()


def refresh_builtin_models():
    """Refresh built-in models (update existing, add new ones)"""
    with get_connection() as conn:
        cursor = conn.cursor()

        for model in BUILTIN_MODELS:
            try:
                # Update if exists, insert if not
                cursor.execute("""
                    INSERT INTO llm_models
                    (name, provider, model_id, base_url, temperature, api_provider, is_builtin, sort_order)
                    VALUES (?, 'OpenAIChatCompletionClient', ?, 'https://openrouter.ai/api/v1', 0.2, ?, 1, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        model_id = excluded.model_id,
                        sort_order = excluded.sort_order,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE is_builtin = 1
                """, (model["name"], model["model_id"], model["api_provider"], model["sort_order"]))
            except Exception as e:
                print(f"Error refreshing model {model['name']}: {e}")

        conn.commit()


# ============ Model Operations ============

def get_all_models(include_builtin: bool = True) -> List[Dict[str, Any]]:
    """Get all models from database"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()

        if include_builtin:
            cursor.execute("SELECT * FROM llm_models ORDER BY sort_order, name")
        else:
            cursor.execute("SELECT * FROM llm_models WHERE is_builtin = 0 ORDER BY name")

        rows = cursor.fetchall()

        models = []
        for row in rows:
            models.append({
                "id": row["id"],
                "name": row["name"],
                "provider": row["provider"],
                "config": {
                    "model": row["model_id"],
                    "temperature": row["temperature"],
                    "base_url": row["base_url"]
                },
                "api_provider": row["api_provider"],
                "is_builtin": bool(row["is_builtin"])
            })
        return models


def get_all_custom_models() -> List[Dict[str, Any]]:
    """Get only custom (non-built-in) models from database"""
    return get_all_models(include_builtin=False)


def get_builtin_models() -> List[Dict[str, Any]]:
    """Get only built-in models from database"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM llm_models WHERE is_builtin = 1 ORDER BY sort_order, name")
        rows = cursor.fetchall()

        models = []
        for row in rows:
            models.append({
                "id": row["id"],
                "name": row["name"],
                "provider": row["provider"],
                "config": {
                    "model": row["model_id"],
                    "temperature": row["temperature"],
                    "base_url": row["base_url"]
                },
                "api_provider": row["api_provider"],
                "is_builtin": True
            })
        return models


def get_model_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific model by name"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM llm_models WHERE name = ?", (name,))
        row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "provider": row["provider"],
                "config": {
                    "model": row["model_id"],
                    "temperature": row["temperature"],
                    "base_url": row["base_url"]
                },
                "api_provider": row["api_provider"],
                "is_builtin": bool(row["is_builtin"])
            }
        return None


# Alias for backwards compatibility
def get_custom_model_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific custom model by name (alias for get_model_by_name)"""
    return get_model_by_name(name)


def add_custom_model(
    name: str,
    model_id: str,
    provider: str = "OpenAIChatCompletionClient",
    base_url: str = "https://openrouter.ai/api/v1",
    temperature: float = 0.2,
    api_provider: str = "OPENROUTER"
) -> bool:
    """Add a new custom model to database"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO llm_models (name, provider, model_id, base_url, temperature, api_provider, is_builtin, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, 0, 999)
            """, (name, provider, model_id, base_url, temperature, api_provider))
            return True
    except sqlite3.IntegrityError:
        # Model with this name already exists
        return False
    except Exception as e:
        print(f"Error adding custom model: {e}")
        return False


def update_model(
    name: str,
    model_id: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    api_provider: Optional[str] = None
) -> bool:
    """Update an existing model (custom only)"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if model_id is not None:
                updates.append("model_id = ?")
                params.append(model_id)
            if provider is not None:
                updates.append("provider = ?")
                params.append(provider)
            if base_url is not None:
                updates.append("base_url = ?")
                params.append(base_url)
            if temperature is not None:
                updates.append("temperature = ?")
                params.append(temperature)
            if api_provider is not None:
                updates.append("api_provider = ?")
                params.append(api_provider)

            if not updates:
                return True  # Nothing to update

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(name)

            # Only update custom models
            query = f"UPDATE llm_models SET {', '.join(updates)} WHERE name = ? AND is_builtin = 0"
            cursor.execute(query, params)
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating model: {e}")
        return False


# Alias for backwards compatibility
def update_custom_model(*args, **kwargs) -> bool:
    return update_model(*args, **kwargs)


def delete_custom_model(name: str) -> bool:
    """Delete a custom model from database (cannot delete built-in models)"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM llm_models WHERE name = ? AND is_builtin = 0", (name,))
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting custom model: {e}")
        return False


def model_exists(name: str) -> bool:
    """Check if a model with the given name exists"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM llm_models WHERE name = ?", (name,))
        return cursor.fetchone() is not None


# ============ Provider Settings Operations ============

def get_provider_settings(provider_name: str) -> Optional[Dict[str, Any]]:
    """Get settings for a specific provider"""
    init_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM provider_settings WHERE provider_name = ?", (provider_name,))
        row = cursor.fetchone()

        if row:
            return {
                "provider_name": row["provider_name"],
                "is_enabled": bool(row["is_enabled"]),
                "base_url": row["base_url"]
            }
        return None


def set_provider_settings(provider_name: str, is_enabled: bool = True, base_url: str = None) -> bool:
    """Set or update provider settings"""
    init_database()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO provider_settings (provider_name, is_enabled, base_url)
                VALUES (?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET
                    is_enabled = excluded.is_enabled,
                    base_url = excluded.base_url,
                    updated_at = CURRENT_TIMESTAMP
            """, (provider_name, int(is_enabled), base_url))
            return True
    except Exception as e:
        print(f"Error setting provider settings: {e}")
        return False


# ============ Migration Helper ============

def migrate_from_json(json_models: List[Dict[str, Any]]) -> int:
    """Migrate custom models from JSON format to SQLite"""
    init_database()
    migrated = 0

    for model in json_models:
        name = model.get("name", "")
        config = model.get("config", {})

        if not name or not config.get("model"):
            continue

        success = add_custom_model(
            name=name,
            model_id=config.get("model", ""),
            provider=model.get("provider", "OpenAIChatCompletionClient"),
            base_url=config.get("base_url", "https://openrouter.ai/api/v1"),
            temperature=config.get("temperature", 0.2),
            api_provider=model.get("api_provider", "OPENROUTER")
        )

        if success:
            migrated += 1

    return migrated


def migrate_from_old_schema():
    """Migrate from old custom_models table to new llm_models table"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='custom_models'")
        if not cursor.fetchone():
            return  # No migration needed

        # Check if new table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_models'")
        if cursor.fetchone():
            # Migrate data from old to new
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO llm_models
                    (name, provider, model_id, base_url, temperature, api_provider, is_builtin, sort_order)
                    SELECT name, provider, model_id, base_url, temperature, api_provider, 0, 999
                    FROM custom_models
                """)
                # Drop old table after migration
                cursor.execute("DROP TABLE IF EXISTS custom_models")
                conn.commit()
                print("Migrated custom_models to llm_models table")
            except Exception as e:
                print(f"Error during schema migration: {e}")
