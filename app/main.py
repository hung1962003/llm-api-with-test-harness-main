"""FastAPI gateway that proxies prompts to a local Ollama instance."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.config import settings
from app.ollama_client import check_ollama_ready, generate_completion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = httpx.Timeout(settings.generate_timeout)
    app.state.http = httpx.AsyncClient(
        base_url=settings.ollama_base_url,
        timeout=timeout,
    )
    logger.info(
        "LLM gateway started (ollama=%s model=%s)",
        settings.ollama_base_url,
        settings.ollama_model,
    )
    try:
        yield
    finally:
        await app.state.http.aclose()
        logger.info("LLM gateway shut down")


app = FastAPI(
    title="Local LLM Gateway API",
    lifespan=lifespan,
)


class GenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Prompt text to feed the LLM",
    )


class GenerateResponse(BaseModel):
    response: str


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(request: Request):
    ready = await check_ollama_ready(request.app.state.http)
    if ready:
        return {"status": "healthy", "ollama_status": "connected"}

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Ollama inference engine is offline or unreachable",
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(body: GenerateRequest, request: Request):
    """Wrap Ollama generation logic into an HTTP POST route."""
    output_text = await generate_completion(request.app.state.http, body.prompt)
    return GenerateResponse(response=output_text)
