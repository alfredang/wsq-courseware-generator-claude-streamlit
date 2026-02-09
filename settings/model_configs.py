"""
Centralized Model Configuration Module

This module manages all AI model configurations for the Courseware system.
All models use Claude via the Anthropic API directly.

Author: Courseware Generator Team
Date: February 2026
"""

from typing import Dict, Any

# =============================================================================
# Claude Model Configurations
# =============================================================================

# Claude Sonnet 4 (Default - Best balance of speed and capability)
claude_sonnet_4_config = {
    "name": "Claude-Sonnet-4",
    "provider": "Anthropic",
    "api_provider": "ANTHROPIC",
    "config": {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.2,
        "max_tokens": 8192,
    },
    "model_info": {
        "family": "anthropic",
        "function_calling": True,
        "json_output": True,
        "vision": True,
        "structured_output": True
    }
}

# Claude Opus 4.5 (Most capable - for complex tasks)
claude_opus_config = {
    "name": "Claude-Opus-4.5",
    "provider": "Anthropic",
    "api_provider": "ANTHROPIC",
    "config": {
        "model": "claude-opus-4-5-20251101",
        "temperature": 0.2,
        "max_tokens": 8192,
    },
    "model_info": {
        "family": "anthropic",
        "function_calling": True,
        "json_output": True,
        "vision": True,
        "structured_output": True
    }
}

# Claude Haiku 3.5 (Fastest - for simple tasks)
claude_haiku_config = {
    "name": "Claude-Haiku-3.5",
    "provider": "Anthropic",
    "api_provider": "ANTHROPIC",
    "config": {
        "model": "claude-3-5-haiku-20241022",
        "temperature": 0.2,
        "max_tokens": 8192,
    },
    "model_info": {
        "family": "anthropic",
        "function_calling": True,
        "json_output": True,
        "vision": True,
        "structured_output": True
    }
}

# Claude Sonnet 3.5 (Previous generation - still excellent)
claude_sonnet_35_config = {
    "name": "Claude-Sonnet-3.5",
    "provider": "Anthropic",
    "api_provider": "ANTHROPIC",
    "config": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.2,
        "max_tokens": 8192,
    },
    "model_info": {
        "family": "anthropic",
        "function_calling": True,
        "json_output": True,
        "vision": True,
        "structured_output": True
    }
}

# =============================================================================
# Default Configuration
# =============================================================================

# Set default to Claude Sonnet 4 (best balance)
default_config = claude_sonnet_4_config

# =============================================================================
# Model Choices Registry
# =============================================================================

MODEL_CHOICES = {
    "Claude-Sonnet-4": claude_sonnet_4_config,
    "Claude-Opus-4.5": claude_opus_config,
    "Claude-Haiku-3.5": claude_haiku_config,
    "Claude-Sonnet-3.5": claude_sonnet_35_config,
}

# =============================================================================
# Configuration Functions
# =============================================================================

def get_model_config(choice: str) -> Dict[str, Any]:
    """
    Return the chosen model config dict.

    Args:
        choice: The model choice string (model name)

    Returns:
        Model configuration dictionary
    """
    # First check static Claude configurations (preferred)
    if choice in MODEL_CHOICES:
        return MODEL_CHOICES[choice]

    # Fallback to default
    return default_config


def get_all_model_choices() -> Dict[str, Dict[str, Any]]:
    """
    Get all available model choices.

    Returns:
        Dictionary of all available models
    """
    return {
        "Claude-Sonnet-4": claude_sonnet_4_config,
        "Claude-Opus-4.5": claude_opus_config,
        "Claude-Haiku-3.5": claude_haiku_config,
        "Claude-Sonnet-3.5": claude_sonnet_35_config,
    }


def get_assessment_default_config() -> Dict[str, Any]:
    """
    Get default model config for Assessment module.

    Returns:
        Model configuration optimized for content generation
    """
    return claude_sonnet_4_config


def get_courseware_default_config() -> Dict[str, Any]:
    """
    Get default model config for Courseware module.

    Returns:
        Model configuration optimized for document generation
    """
    return claude_sonnet_4_config


def get_cp_default_config() -> Dict[str, Any]:
    """
    Get default model config for Course Proposal module.

    Returns:
        Model configuration optimized for extraction and analysis
    """
    return claude_sonnet_4_config


def get_fast_model_config() -> Dict[str, Any]:
    """
    Get fastest model config for simple tasks.

    Returns:
        Model configuration optimized for speed
    """
    return claude_haiku_config


def get_powerful_model_config() -> Dict[str, Any]:
    """
    Get most powerful model config for complex tasks.

    Returns:
        Model configuration optimized for capability
    """
    return claude_opus_config
