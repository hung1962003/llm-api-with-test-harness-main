"""Negative / validation tests for /generate."""

from fastapi.testclient import TestClient

from app.main import app


def test_empty_prompt_rejected():
    """Empty prompt triggers a Pydantic validation error (422)."""
    with TestClient(app) as client:
        response = client.post("/generate", json={"prompt": ""})
    assert response.status_code == 422


def test_invalid_json_payload():
    """Malformed non-JSON content should be rejected by FastAPI."""
    with TestClient(app) as client:
        response = client.post(
            "/generate",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 422


def test_prompt_over_max_length_rejected():
    """Prompts longer than 500 characters are rejected."""
    with TestClient(app) as client:
        response = client.post("/generate", json={"prompt": "l" * 501})
    assert response.status_code == 422
