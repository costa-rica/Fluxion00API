"""
Base LLM provider interface for Fluxion00API.

This module defines the abstract base class for LLM providers,
allowing for easy swapping between different LLM services (Ollama, OpenAI, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """Represents a message in the conversation."""
    role: str  # 'system', 'user', or 'assistant'
    content: str


@dataclass
class LLMResponse:
    """Represents a response from an LLM provider."""
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers (Ollama, OpenAI, etc.) should inherit from this class
    and implement the required methods.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the API endpoint
        """
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion from a single prompt.

        Args:
            prompt: The input prompt
            model: Model identifier (provider-specific)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse: The generated response
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion from a conversation history.

        Args:
            messages: List of conversation messages
            model: Model identifier (provider-specific)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse: The generated response
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a completion with streaming response.

        Args:
            prompt: The input prompt
            model: Model identifier (provider-specific)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Yields:
            str: Chunks of the generated response
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List[str]: List of model identifiers
        """
        pass

    def format_prompt_with_system(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Helper method to combine system prompt with user prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            str: Combined prompt
        """
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt
