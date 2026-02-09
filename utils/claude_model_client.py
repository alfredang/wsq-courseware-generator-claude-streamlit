"""
Claude Model Client - Claude Agent SDK (Subscription-based)

This module provides a unified interface for Claude models using the Claude Agent SDK.
Uses your Claude Pro/Max subscription instead of API credits.

To use subscription: Run `claude login` and select "Log in with your subscription account"

Author: Courseware Generator Team
Date: February 2026
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Claude Agent SDK not available in production - use Anthropic API
CLAUDE_SDK_AVAILABLE = False

# Fallback to Anthropic API if SDK not available
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# =============================================================================
# Response Classes (OpenAI SDK compatible)
# =============================================================================

@dataclass
class MessageContent:
    """Mimics OpenAI's message content structure."""
    content: str
    role: str = "assistant"


@dataclass
class Choice:
    """Mimics OpenAI's choice structure."""
    message: MessageContent
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class CompletionResponse:
    """Mimics OpenAI's completion response structure."""
    choices: List[Choice]
    model: str
    id: str = "claude-response"

    @classmethod
    def from_text(cls, text: str, model: str) -> "CompletionResponse":
        """Create from plain text response."""
        return cls(
            choices=[Choice(message=MessageContent(content=text))],
            model=model,
            id="claude-sdk-response"
        )


# =============================================================================
# Claude Agent SDK Wrapper (Subscription-based)
# =============================================================================

class ClaudeSDKCompletions:
    """Wrapper using Claude Agent SDK (uses subscription, not API credits)."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self._model = model

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 8192,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Create a chat completion using Claude Agent SDK (subscription).

        Mimics OpenAI's client.chat.completions.create() interface.
        """
        # Build prompt from messages
        system_message = ""
        conversation = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation.append(f"{msg['role'].upper()}: {msg['content']}")

        # Add JSON instruction if requested
        if response_format and response_format.get("type") == "json_object":
            system_message += "\n\nIMPORTANT: You must respond with valid JSON only. No markdown, no code blocks, just raw JSON."

        # Build full prompt
        full_prompt = ""
        if system_message:
            full_prompt = f"SYSTEM: {system_message}\n\n"
        full_prompt += "\n".join(conversation)

        # Run async query
        response_text = asyncio.get_event_loop().run_until_complete(
            self._query_claude(full_prompt, model)
        )

        return CompletionResponse.from_text(response_text, model)

    async def _query_claude(self, prompt: str, model: str) -> str:
        """Query Claude using the Agent SDK."""
        if not CLAUDE_SDK_AVAILABLE:
            raise RuntimeError("Claude Agent SDK not available. Install with: pip install claude-agent-sdk")

        response_parts = []
        async for message in claude_query(
            prompt=prompt,
            options={"model": model}
        ):
            # Collect response parts
            if hasattr(message, 'content'):
                response_parts.append(str(message.content))
            elif isinstance(message, str):
                response_parts.append(message)

        return "".join(response_parts)


class ClaudeSDKChat:
    """Chat wrapper for Claude Agent SDK."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.completions = ClaudeSDKCompletions(model)


class ClaudeSubscriptionClient:
    """
    Claude client using subscription (via Claude Agent SDK).

    Uses your Claude Pro/Max subscription instead of API credits.

    Usage:
        client = ClaudeSubscriptionClient()
        response = client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.2
        )
        content = response.choices[0].message.content
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514", **kwargs):
        self._model = model
        self.chat = ClaudeSDKChat(model)


# =============================================================================
# Fallback: Anthropic API Client (API credits)
# =============================================================================

class AnthropicAPICompletions:
    """Wrapper using Anthropic API directly (uses API credits)."""

    def __init__(self, client):
        self._client = client

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 8192,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> CompletionResponse:
        """Create completion using Anthropic API."""
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        if response_format and response_format.get("type") == "json_object":
            json_instruction = "\n\nIMPORTANT: You must respond with valid JSON only. No markdown, no code blocks, just raw JSON."
            system_message = (system_message or "You are a helpful assistant.") + json_instruction

        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_message or "You are a helpful assistant.",
            messages=user_messages,
            temperature=temperature
        )

        content = response.content[0].text if response.content else ""
        return CompletionResponse.from_text(content, model)


class AnthropicAPIChat:
    """Chat wrapper for Anthropic API."""

    def __init__(self, client):
        self.completions = AnthropicAPICompletions(client)


class AnthropicAPIClient:
    """Fallback client using Anthropic API (API credits)."""

    def __init__(self, api_key: str, **kwargs):
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("Anthropic SDK not available. Install with: pip install anthropic")
        self._anthropic = Anthropic(api_key=api_key)
        self.chat = AnthropicAPIChat(self._anthropic)


# =============================================================================
# Model Configuration
# =============================================================================

CLAUDE_MODELS = {
    "Claude-Sonnet-4": "claude-sonnet-4-20250514",
    "Claude-Opus-4.5": "claude-opus-4-5-20251101",
    "Claude-Haiku-3.5": "claude-3-5-haiku-20241022",
    "Claude-Sonnet-3.5": "claude-3-5-sonnet-20241022",
    # Legacy aliases (backward compatibility)
    "DeepSeek-Chat": "claude-sonnet-4-20250514",
    "GPT-4o-Mini": "claude-3-5-haiku-20241022",
    "Gemini-Flash": "claude-3-5-haiku-20241022",
    "default": "claude-sonnet-4-20250514"
}


def get_claude_model_id(model_choice: str) -> str:
    """Get the full Claude model ID from a model choice string."""
    if model_choice.startswith("claude-"):
        return model_choice
    return CLAUDE_MODELS.get(model_choice, CLAUDE_MODELS["default"])


# =============================================================================
# Configuration: Choose Subscription vs API
# =============================================================================

# Set to True to use subscription (Claude Pro/Max) - requires claude-agent-sdk
# Set to False to use API credits via Anthropic API
USE_SUBSCRIPTION = False


# =============================================================================
# Main Factory Function
# =============================================================================

def create_llm_client(model_choice: str = "Claude-Sonnet-4"):
    """
    Create a Claude client configured with the specified model choice.

    Uses Claude subscription (Pro/Max) by default. Falls back to API if SDK unavailable.

    Args:
        model_choice: Model choice string (e.g., "Claude-Sonnet-4", "Claude-Opus-4.5")

    Returns:
        tuple: (Client instance, model configuration dict)

    Example:
        >>> client, config = create_llm_client("Claude-Sonnet-4")
        >>> response = client.chat.completions.create(
        ...     model=config["model"],
        ...     temperature=config["temperature"],
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
        >>> content = response.choices[0].message.content
    """
    model_id = get_claude_model_id(model_choice)

    model_config = {
        "model": model_id,
        "temperature": 0.2,
        "max_tokens": 8192
    }

    # Try subscription-based client first
    if USE_SUBSCRIPTION and CLAUDE_SDK_AVAILABLE:
        print(f"Using Claude subscription for {model_choice}")
        client = ClaudeSubscriptionClient(model=model_id)
        return client, model_config

    # Fallback to API
    if ANTHROPIC_AVAILABLE:
        print(f"Using Anthropic API for {model_choice} (API credits)")
        from settings.api_manager import load_api_keys
        api_keys = load_api_keys()
        api_key = api_keys.get("ANTHROPIC_API_KEY", "")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set USE_SUBSCRIPTION=True or add API key.")

        client = AnthropicAPIClient(api_key=api_key)
        return client, model_config

    raise RuntimeError("No Claude client available. Install claude-agent-sdk or anthropic.")


def get_model_name(model_choice: str) -> str:
    """Get the Claude model ID from a model choice string."""
    return get_claude_model_id(model_choice)


# =============================================================================
# Convenience: Direct Async Query (for simple use cases)
# =============================================================================

async def query_claude(prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
    """
    Simple async function to query Claude using subscription.

    Args:
        prompt: The prompt to send
        model: Model ID to use

    Returns:
        str: Claude's response text
    """
    if not CLAUDE_SDK_AVAILABLE:
        raise RuntimeError("Claude Agent SDK not available")

    response_parts = []
    async for message in claude_query(prompt=prompt, options={"model": model}):
        if hasattr(message, 'content'):
            response_parts.append(str(message.content))
        elif isinstance(message, str):
            response_parts.append(message)

    return "".join(response_parts)
