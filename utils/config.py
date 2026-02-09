"""
Configuration Module

Provides unified configuration loading from multiple sources:
1. Environment variables
2. .env file (via python-dotenv)
3. Streamlit secrets (if available)

Author: Courseware Generator Team
Date: February 2026
"""

import os
from typing import Optional, Dict, Any

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_secret(key: str, default: str = "") -> str:
    """
    Get a secret value from environment variables.

    Args:
        key: The secret key name
        default: Default value if not found

    Returns:
        The secret value
    """
    return os.environ.get(key, default)


def get_secret_section(section: str) -> Optional[Dict[str, Any]]:
    """
    Get a section from Streamlit secrets (for nested TOML sections).

    Args:
        section: The section name (e.g., 'GOOGLE_SERVICE_ACCOUNT')

    Returns:
        Dictionary of section values or None
    """
    # Try to load from environment variable as JSON
    import json
    env_value = os.environ.get(f"{section}_JSON", "")
    if env_value:
        try:
            return json.loads(env_value)
        except json.JSONDecodeError:
            pass

    return None


# Convenience functions for common secrets
def get_anthropic_api_key() -> str:
    """Get Anthropic API key."""
    return get_secret("ANTHROPIC_API_KEY")


def get_database_url() -> str:
    """Get database URL."""
    return get_secret("DATABASE_URL")


def get_admin_username() -> str:
    """Get admin username."""
    return get_secret("ADMIN_USERNAME", "admin")


def get_admin_password() -> str:
    """Get admin password."""
    return get_secret("ADMIN_PASSWORD")


def get_google_service_account() -> Optional[Dict[str, Any]]:
    """Get Google service account credentials."""
    return get_secret_section("GOOGLE_SERVICE_ACCOUNT")
