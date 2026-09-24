"""API behaviour tests for /health and /generate (mocked Ollama)."""

from __future__ import annotations

import httpx
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_healthy(monkeypatch):
    """Verify /health returns 200 when Ollama is reachable."""

    async def mock_ready(client):
        return True

    monkeypatch.setattr("app.main.check_ollama_ready", mock_ready)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "ollama_status": "connected"}


def test_health_endpoint_ollama_unreachable(monkeypatch):
    """Verify /health returns 503 when Ollama can't be reached."""

    async def mock_ready(client):
        return False

    monkeypatch.setattr("app.main.check_ollama_ready", mock_ready)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503


def test_generate_success(monkeypatch):
    """Verify /generate returns model text on success."""

    async def mock_generate(client, prompt: str) -> str:
        assert prompt == "hello"
        return "world"

    monkeypatch.setattr("app.main.generate_completion", mock_generate)

    with TestClient(app) as client:
        response = client.post("/generate", json={"prompt": "hello"})

    assert response.status_code == 200
    assert response.json() == {"response": "world"}


def test_generate_ollama_down(monkeypatch):
    """Verify /generate maps connection failures to 503."""

    async def mock_generate(client, prompt: str) -> str:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to local Ollama service",
        )

    monkeypatch.setattr("app.main.generate_completion", mock_generate)

    with TestClient(app) as client:
        response = client.post("/generate", json={"prompt": "hello"})

    assert response.status_code == 503


def test_generate_timeout(monkeypatch):
    """Verify /generate maps inference timeouts to 504."""

    async def mock_generate(client, prompt: str) -> str:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out while waiting for local LLM inference",
        )

    monkeypatch.setattr("app.main.generate_completion", mock_generate)

    with TestClient(app) as client:
        response = client.post("/generate", json={"prompt": "hello"})

    assert response.status_code == 504
