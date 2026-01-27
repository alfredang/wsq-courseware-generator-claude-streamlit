"""
OpenAI Model Client Bridge for Autogen Config Compatibility.

This module provides an adapter to bridge existing Autogen model configurations
with the OpenAI SDK, allowing seamless transition from Autogen to OpenAI SDK.

Author: Migration from Autogen to OpenAI SDK
Date: 2026-01-20
"""

from openai import OpenAI
from typing import Dict, Any
from settings.model_configs import get_model_config
from settings.api_manager import load_api_keys


def create_openai_client(model_choice: str) -> tuple[OpenAI, Dict[str, Any]]:
    """
    Create an OpenAI client configured with the specified model choice.

    This function bridges the existing Autogen model configuration system
    with the OpenAI SDK by extracting configuration parameters from the
    Autogen config format.

    Args:
        model_choice: Model choice string (e.g., "DeepSeek-Chat", "GPT-4o-Mini")

    Returns:
        tuple: (OpenAI client instance, model configuration dict)
            - OpenAI client: Configured with base_url and api_key
            - Config dict: Contains model name, temperature, and other settings

    Example:
        >>> client, config = create_openai_client("DeepSeek-Chat")
        >>> model_name = config["model"]
        >>> temperature = config["temperature"]
    """
    # Get Autogen-style config
    autogen_config = get_model_config(model_choice)

    # Extract configuration from Autogen format
    config_dict = autogen_config.get("config", {})

    base_url = config_dict.get("base_url", "https://openrouter.ai/api/v1")
    api_key = config_dict.get("api_key", "")
    model = config_dict.get("model", "deepseek/deepseek-chat")
    temperature = config_dict.get("temperature", 0.2)

    # Fallback: If no API key in config, get it dynamically based on api_provider
    if not api_key:
        api_provider = autogen_config.get("api_provider", "OPENROUTER")
        api_keys = load_api_keys()
        api_key = api_keys.get(f"{api_provider}_API_KEY", "")

    # Create OpenAI client with extracted configuration
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    # Return both client and configuration for use in API calls
    model_config = {
        "model": model,
        "temperature": temperature,
        "base_url": base_url
    }

    return client, model_config


def get_model_name(model_choice: str) -> str:
    """
    Extract just the model name from the configuration.

    Args:
        model_choice: Model choice string

    Returns:
        str: The model identifier (e.g., "deepseek/deepseek-chat")
    """
    autogen_config = get_model_config(model_choice)
    return autogen_config.get("config", {}).get("model", "deepseek/deepseek-chat")
