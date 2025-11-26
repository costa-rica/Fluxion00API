"""
LLM Provider Factory for Fluxion00API.

This module provides a factory function to create LLM provider instances
based on provider type and model selection.
"""

from typing import Optional
from .base import BaseLLMProvider
from .ollama_client import OllamaProvider
from .openai_client import OpenAIProvider
from src.utils import logger


def get_provider(
    provider_type: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> BaseLLMProvider:
    """
    Factory function to create an LLM provider instance.

    This function creates the appropriate provider based on the provider_type.
    The model parameter is passed directly to the provider without validation,
    allowing the LLM API to validate model availability.

    Args:
        provider_type: Type of provider ("ollama" or "openai")
        model: Model identifier (e.g., "gpt-4o-mini", "mistral:instruct")
               If not provided, uses provider's default model
        api_key: Optional API key (reads from env if not provided)
        base_url: Optional base URL (reads from env if not provided)

    Returns:
        BaseLLMProvider: Configured provider instance

    Raises:
        ValueError: If provider_type is not recognized

    Examples:
        >>> # Create OpenAI provider with specific model
        >>> provider = get_provider("openai", model="gpt-4o-mini")
        >>>
        >>> # Create Ollama provider with default model
        >>> provider = get_provider("ollama")
        >>>
        >>> # Create with custom API key
        >>> provider = get_provider("openai", model="gpt-4-turbo", api_key="sk-...")
    """
    provider_type = provider_type.lower()

    # Log provider creation
    logger.info(f"[PROVIDER] Creating {provider_type} provider with model: {model or 'default'}")

    if provider_type == "ollama":
        # Create Ollama provider
        default_model = model or "mistral:instruct"
        return OllamaProvider(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model
        )

    elif provider_type == "openai":
        # Create OpenAI provider
        default_model = model or "gpt-4o-mini"
        return OpenAIProvider(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model
        )

    else:
        # Unknown provider type
        raise ValueError(
            f"Unknown provider type: '{provider_type}'. "
            f"Supported providers: 'ollama', 'openai'"
        )


def get_provider_info(provider: BaseLLMProvider) -> dict:
    """
    Get information about a provider instance.

    Args:
        provider: Provider instance

    Returns:
        dict: Provider information including type, model, and available models

    Example:
        >>> provider = get_provider("openai", model="gpt-4o-mini")
        >>> info = get_provider_info(provider)
        >>> print(info)
        {'type': 'openai', 'model': 'gpt-4o-mini', 'available_models': [...]}
    """
    provider_type = None
    if isinstance(provider, OllamaProvider):
        provider_type = "ollama"
    elif isinstance(provider, OpenAIProvider):
        provider_type = "openai"

    return {
        "type": provider_type,
        "model": provider.default_model,
        "available_models": provider.get_available_models()
    }
