"""
Ollama LLM provider implementation for Fluxion00API.

This module provides integration with the Ollama API for local LLM inference.
"""

import os
import httpx
from typing import List, Optional, AsyncIterator, Dict, Any
from .base import BaseLLMProvider, LLMMessage, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider implementation.

    This provider connects to an Ollama API endpoint (local or remote)
    and provides access to models like mistral:instruct.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "mistral:instruct",
        timeout: float = 120.0
    ):
        """
        Initialize the Ollama provider.

        Args:
            api_key: API key for authentication (reads from KEY_OLLAMA env var if not provided)
            base_url: Base URL for Ollama API (reads from URL_BASE_OLLAMA env var if not provided)
            default_model: Default model to use (default: "mistral:instruct")
            timeout: Request timeout in seconds (default: 120.0)
        """
        api_key = api_key or os.getenv('KEY_OLLAMA')
        base_url = base_url or os.getenv('URL_BASE_OLLAMA')

        super().__init__(api_key=api_key, base_url=base_url)

        if not self.base_url:
            raise ValueError(
                "Base URL must be provided either as argument or through "
                "URL_BASE_OLLAMA environment variable"
            )

        self.default_model = default_model
        self.timeout = timeout
        self.api_endpoint = f"{self.base_url.rstrip('/')}/api/generate"

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for Ollama API requests.

        Returns:
            Dict[str, str]: Headers dictionary
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

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
        Generate a completion from a single prompt using Ollama.

        Args:
            prompt: The input prompt
            model: Model identifier (default: mistral:instruct)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional Ollama-specific parameters

        Returns:
            LLMResponse: The generated response

        Example:
            >>> provider = OllamaProvider()
            >>> response = await provider.generate("Hello, how are you?")
            >>> print(response.content)
        """
        model = model or self.default_model

        # Combine system prompt with user prompt if provided
        full_prompt = self.format_prompt_with_system(prompt, system_prompt)

        # Build request payload
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Add any additional kwargs to options
        for key, value in kwargs.items():
            payload["options"][key] = value

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
        return LLMResponse(
            content=data.get("response", ""),
            model=data.get("model", model),
            finish_reason=data.get("done_reason"),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
            },
            raw_response=data
        )

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

        Note: Ollama's /api/generate endpoint doesn't natively support chat format,
        so we convert the messages into a single prompt.

        Args:
            messages: List of conversation messages
            model: Model identifier (default: mistral:instruct)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama-specific parameters

        Returns:
            LLMResponse: The generated response

        Example:
            >>> messages = [
            ...     LLMMessage(role="system", content="You are a helpful assistant."),
            ...     LLMMessage(role="user", content="What is Python?")
            ... ]
            >>> response = await provider.chat(messages)
        """
        # Convert chat messages to a single prompt
        prompt_parts = []
        system_prompt = None

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        # Add final assistant prompt
        prompt_parts.append("Assistant:")
        prompt = "\n\n".join(prompt_parts)

        return await self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            **kwargs
        )

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
            model: Model identifier (default: mistral:instruct)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional Ollama-specific parameters

        Yields:
            str: Chunks of the generated response

        Example:
            >>> async for chunk in provider.stream_generate("Tell me a story"):
            ...     print(chunk, end="", flush=True)
        """
        model = model or self.default_model

        # Combine system prompt with user prompt if provided
        full_prompt = self.format_prompt_with_system(prompt, system_prompt)

        # Build request payload
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Add any additional kwargs to options
        for key, value in kwargs.items():
            payload["options"][key] = value

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
                    if line.strip():
                        import json
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue

    def get_available_models(self) -> List[str]:
        """
        Get list of available models for Ollama.

        Note: This is a static list. In production, you might want to
        query the Ollama API's /api/tags endpoint.

        Returns:
            List[str]: List of common Ollama model identifiers
        """
        return [
            "mistral:instruct",
            "llama2",
            "llama2:13b",
            "codellama",
            "phi",
            "neural-chat",
        ]

    async def test_connection(self) -> bool:
        """
        Test the connection to the Ollama API.

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
def get_ollama_provider(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    default_model: str = "mistral:instruct"
) -> OllamaProvider:
    """
    Factory function to create an Ollama provider instance.

    Args:
        api_key: API key for authentication (reads from env if not provided)
        base_url: Base URL for Ollama API (reads from env if not provided)
        default_model: Default model to use

    Returns:
        OllamaProvider: Configured Ollama provider instance
    """
    return OllamaProvider(
        api_key=api_key,
        base_url=base_url,
        default_model=default_model
    )
