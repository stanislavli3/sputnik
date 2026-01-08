"""Base LLM client interface and implementations."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"


class LLMClient(ABC):
    """Base interface for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Generate text stream from a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Text chunks as they are generated
        """
        pass


def create_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> LLMClient:
    """
    Create an LLM client based on configuration.

    Args:
        provider: LLM provider name (defaults to OLLAMA)
        model: Model name (e.g., "llama3", "mistral")
        base_url: Base URL for the LLM service
        api_key: API key (if required)
        **kwargs: Additional provider-specific parameters

    Returns:
        Configured LLM client
    """
    import os

    # Get provider from environment or parameter
    provider_name = provider or os.getenv("LLM_PROVIDER", "ollama").lower()
    model_name = model or os.getenv("LLM_MODEL", "llama3")
    base_url_env = base_url or os.getenv("LLM_BASE_URL")
    api_key_env = api_key or os.getenv("LLM_API_KEY")

    if provider_name == LLMProvider.OLLAMA:
        from sputnik.llm.ollama_client import OllamaClient

        ollama_url = base_url_env or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaClient(model=model_name, base_url=ollama_url, **kwargs)
    elif provider_name == LLMProvider.HUGGINGFACE:
        # HuggingFace integration can be added later
        raise ValueError("HuggingFace provider not yet implemented")
    elif provider_name == LLMProvider.OPENROUTER:
        from sputnik.llm.openrouter_client import OpenRouterClient

        openrouter_url = base_url_env or "https://openrouter.ai/api/v1"
        return OpenRouterClient(
            model=model_name, base_url=openrouter_url, api_key=api_key_env, **kwargs
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
