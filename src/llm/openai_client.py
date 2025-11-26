"""
OpenAI LLM provider implementation for Fluxion00API.

This module provides integration with the OpenAI API for GPT models.
"""

import os
import httpx
import json
from typing import List, Optional, AsyncIterator, Dict, Any
from .base import BaseLLMProvider, LLMMessage, LLMResponse
from src.utils import logger, truncate_text


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider implementation.

    This provider connects to the OpenAI API and provides access to GPT models
    like gpt-4o-mini, gpt-4-turbo, etc.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        timeout: float = 120.0
    ):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: API key for authentication (reads from KEY_OPENAI env var if not provided)
            base_url: Base URL for OpenAI API (reads from URL_BASE_OPENAI env var if not provided)
            default_model: Default model to use (default: "gpt-4o-mini")
            timeout: Request timeout in seconds (default: 120.0)
        """
        api_key = api_key or os.getenv('KEY_OPENAI')
        base_url = base_url or os.getenv('URL_BASE_OPENAI', 'https://api.openai.com/v1')

        super().__init__(api_key=api_key, base_url=base_url)

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as argument or through "
                "KEY_OPENAI environment variable"
            )

        self.default_model = default_model
        self.timeout = timeout
        self.api_endpoint = f"{self.base_url.rstrip('/')}/chat/completions"

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for OpenAI API requests.

        Returns:
            Dict[str, str]: Headers dictionary
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

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
        Generate a completion from a single prompt using OpenAI.

        Args:
            prompt: The input prompt
            model: Model identifier (default: gpt-4o-mini)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            LLMResponse: The generated response

        Example:
            >>> provider = OpenAIProvider()
            >>> response = await provider.generate("Hello, how are you?")
            >>> print(response.content)
        """
        model = model or self.default_model

        # Build messages list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Log LLM call
        logger.info(f"[LLM] Making call to OpenAI...")
        logger.info(f"[LLM] Model: {model} | Prompt length: {len(prompt)} chars | Preview: \"{truncate_text(prompt)}\"")

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add any additional kwargs
        for key, value in kwargs.items():
            payload[key] = value

        # Make API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_endpoint,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

        # Parse response
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})

        llm_response = LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", model),
            finish_reason=choice.get("finish_reason"),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            raw_response=data
        )

        # Log response
        logger.info(f"[LLM] Response length: {len(llm_response.content)} chars | Tokens: {usage.get('total_tokens', 0)}")

        return llm_response

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
            model: Model identifier (default: gpt-4o-mini)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            LLMResponse: The generated response

        Example:
            >>> messages = [
            ...     LLMMessage(role="system", content="You are a helpful assistant."),
            ...     LLMMessage(role="user", content="What is Python?")
            ... ]
            >>> response = await provider.chat(messages)
        """
        model = model or self.default_model

        # Convert LLMMessage objects to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Log LLM call
        total_length = sum(len(msg.content) for msg in messages)
        logger.info(f"[LLM] Making chat call to OpenAI...")
        logger.info(f"[LLM] Model: {model} | Messages: {len(messages)} | Total length: {total_length} chars")

        # Build request payload
        payload = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add any additional kwargs
        for key, value in kwargs.items():
            payload[key] = value

        # Make API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_endpoint,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

        # Parse response
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})

        llm_response = LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", model),
            finish_reason=choice.get("finish_reason"),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            raw_response=data
        )

        # Log response
        logger.info(f"[LLM] Response length: {len(llm_response.content)} chars | Tokens: {usage.get('total_tokens', 0)}")

        return llm_response

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
            model: Model identifier (default: gpt-4o-mini)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional OpenAI-specific parameters

        Yields:
            str: Chunks of the generated response

        Example:
            >>> async for chunk in provider.stream_generate("Tell me a story"):
            ...     print(chunk, end="", flush=True)
        """
        model = model or self.default_model

        # Build messages list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True  # Enable streaming
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add any additional kwargs
        for key, value in kwargs.items():
            payload[key] = value

        # Make streaming API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self.api_endpoint,
                json=payload,
                headers=self._get_headers()
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        # Skip [DONE] marker
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")

                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    def get_available_models(self) -> List[str]:
        """
        Get list of available models for OpenAI.

        Note: This is a static list of common models. The backend accepts
        any model string and lets OpenAI API validate it.

        Returns:
            List[str]: List of common OpenAI model identifiers
        """
        return [
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    async def test_connection(self) -> bool:
        """
        Test the connection to the OpenAI API.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            response = await self.generate("Hello", max_tokens=5)
            return bool(response.content)
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


# Factory function for easy instantiation
def get_openai_provider(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    default_model: str = "gpt-4o-mini"
) -> OpenAIProvider:
    """
    Factory function to create an OpenAI provider instance.

    Args:
        api_key: API key for authentication (reads from env if not provided)
        base_url: Base URL for OpenAI API (reads from env if not provided)
        default_model: Default model to use

    Returns:
        OpenAIProvider: Configured OpenAI provider instance
    """
    return OpenAIProvider(
        api_key=api_key,
        base_url=base_url,
        default_model=default_model
    )
