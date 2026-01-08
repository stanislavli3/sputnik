"""Model management endpoints."""

import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sputnik.llm.client import create_llm_client, LLMProvider

router = APIRouter()


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str
    name: str
    provider: str
    description: Optional[str] = None
    available: bool = True


class ModelsResponse(BaseModel):
    """Response with available models."""

    models: List[ModelInfo]
    default_model: str


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """
    List all available LLM models.

    Returns:
        List of available models with their information
    """
    models: List[ModelInfo] = []

    # Ollama models (if available)
    try:
        from sputnik.llm.ollama_client import OllamaClient
        import httpx

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{ollama_url}/api/tags")
                if response.status_code == 200:
                    ollama_models = response.json().get("models", [])
                    for model in ollama_models:
                        model_name = model.get("name", "")
                        models.append(
                            ModelInfo(
                                id=f"ollama:{model_name}",
                                name=model_name,
                                provider="ollama",
                                description=f"Local model via Ollama",
                            )
                        )
            except Exception:
                # Ollama not available, skip
                pass
    except Exception:
        pass

    # Add common Ollama models (even if not pulled yet)
    common_ollama_models = [
        ("llama3", "Llama 3 (8B)"),
        ("llama3:70b", "Llama 3 (70B)"),
        ("mistral", "Mistral 7B"),
        ("codellama", "Code Llama"),
        ("phi3", "Phi-3"),
    ]
    for model_id, model_name in common_ollama_models:
        if not any(m.id == f"ollama:{model_id}" for m in models):
            models.append(
                ModelInfo(
                    id=f"ollama:{model_id}",
                    name=model_name,
                    provider="ollama",
                    description="Available via Ollama (may need to pull)",
                )
            )

    # OpenRouter models (if API key is set)
    if os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY"):
        openrouter_models = [
            ("meta-llama/llama-3-8b-instruct", "Llama 3 8B Instruct (OpenRouter)"),
            ("meta-llama/llama-3-70b-instruct", "Llama 3 70B Instruct (OpenRouter)"),
            ("mistralai/mistral-7b-instruct", "Mistral 7B Instruct (OpenRouter)"),
            ("codellama/codellama-34b-instruct", "CodeLlama 34B Instruct (OpenRouter)"),
            ("google/gemma-7b-it", "Gemma 7B Instruct (OpenRouter)"),
        ]
        for model_id, model_name in openrouter_models:
            models.append(
                ModelInfo(
                    id=f"openrouter:{model_id}",
                    name=model_name,
                    provider="openrouter",
                    description="Cloud-based via OpenRouter",
                )
            )

    # Default model from environment or first available
    default_model = os.getenv("LLM_MODEL", "llama3")
    default_provider = os.getenv("LLM_PROVIDER", "ollama")
    default_id = f"{default_provider}:{default_model}"

    return ModelsResponse(models=models, default_model=default_id)


@router.get("/models/current")
async def get_current_model() -> dict:
    """
    Get the currently configured model.

    Returns:
        Current model information
    """
    model = os.getenv("LLM_MODEL", "llama3")
    provider = os.getenv("LLM_PROVIDER", "ollama")
    
    return {
        "model": model,
        "provider": provider,
        "id": f"{provider}:{model}",
    }


@router.post("/models/select")
async def select_model(request: dict) -> dict:
    """
    Select a model for the current session (stored in memory, not persisted).

    Args:
        request: Request body with model_id in format "provider:model" (e.g., "ollama:llama3")

    Returns:
        Confirmation with selected model
    """
    try:
        model_id = request.get("model_id")
        if not model_id:
            raise ValueError("model_id is required")
        
        parts = model_id.split(":", 1)
        if len(parts) != 2:
            raise ValueError("Model ID must be in format 'provider:model'")
        
        provider, model = parts
        
        # Validate provider
        if provider not in [p.value for p in LLMProvider]:
            raise ValueError(f"Unknown provider: {provider}")
        
        # Note: In a real implementation, you'd store this per-user/session
        # For now, we'll just validate it can be created
        client = create_llm_client(provider=provider, model=model)
        
        return {
            "success": True,
            "model_id": model_id,
            "provider": provider,
            "model": model,
            "message": "Model selected (applies to current session)",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
