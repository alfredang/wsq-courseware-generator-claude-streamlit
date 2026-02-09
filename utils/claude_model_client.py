"""
Claude Model Reference - Model ID Mapping

This module provides model ID mapping for Claude models.
Used by Claude Code skills for reference when generating content.

No API calls are made from this module.
"""

# Claude model ID mapping
CLAUDE_MODELS = {
    "Claude-Sonnet-4": "claude-sonnet-4-20250514",
    "Claude-Opus-4.5": "claude-opus-4-5-20251101",
    "Claude-Haiku-3.5": "claude-3-5-haiku-20241022",
    "Claude-Sonnet-3.5": "claude-3-5-sonnet-20241022",
    "default": "claude-sonnet-4-20250514",
}


def get_claude_model_id(model_choice: str) -> str:
    """Get the full Claude model ID from a model choice string."""
    if model_choice.startswith("claude-"):
        return model_choice
    return CLAUDE_MODELS.get(model_choice, CLAUDE_MODELS["default"])
