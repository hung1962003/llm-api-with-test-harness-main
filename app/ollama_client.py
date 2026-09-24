"""Async HTTP helpers for talking to a local Ollama instance."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


async def check_ollama_ready(client: httpx.AsyncClient) -> bool:
    """Return True when Ollama responds 200 on /api/tags."""
    try:
        response = await client.get(
            "/api/tags",
            timeout=settings.health_timeout,
        )
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return False


async def generate_completion(client: httpx.AsyncClient, prompt: str) -> str:
    """Send a non-streaming generate request to Ollama and return the text."""
    try:
        response = await client.post(
            "/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=settings.generate_timeout,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response")
        if text is None:
            logger.error("Ollama response missing 'response' field: %s", data)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama returned an unexpected response payload",
            )
        return text

    except httpx.TimeoutException:
        logger.warning("Ollama generate timed out after %ss", settings.generate_timeout)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out while waiting for local LLM inference",
        ) from None
    except httpx.ConnectError:
        logger.warning("Failed to connect to Ollama at %s", settings.ollama_base_url)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to local Ollama service",
        ) from None
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Ollama HTTP %s for /api/generate",
            exc.response.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an error response",
        ) from None
