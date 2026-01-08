"""OpenRouter client for open source LLMs via API."""

import json
from typing import Any, AsyncGenerator, Optional

import httpx


class OpenRouterClient:
    """Client for OpenRouter API (access to many open source models)."""

    def __init__(
        self,
        model: str = "meta-llama/llama-3-8b-instruct",
        base_url: str = "https://openrouter.ai/api/v1",
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        """
        Initialize OpenRouter client.

        Args:
            model: Model name (e.g., "meta-llama/llama-3-8b-instruct")
            base_url: OpenRouter API URL
            api_key: OpenRouter API key
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self.client = httpx.AsyncClient(timeout=timeout, headers=headers)

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
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            payload.update(kwargs)

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenRouter API error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to generate text: {e}") from e

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text stream from a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            payload.update(kwargs)

            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenRouter API error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to generate text stream: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
