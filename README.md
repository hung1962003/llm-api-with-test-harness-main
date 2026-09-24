# Local LLM API Gateway

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local-orange.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An asynchronous API gateway built with **FastAPI** that routes prompts to a local **Ollama** inference engine. Focused on resilience, predictable error handling, and load benchmarking.

---

## Key Features

- **Health monitoring** — `GET /health` verifies Ollama via `/api/tags` without running inference
- **Resilient timeouts** — configurable async timeouts (health + generate) so slow LLM calls cannot stall Uvicorn
- **Structured errors** — maps upstream failures to `503` / `504` / `500` instead of opaque crashes
- **Load tested** — Locust harness documents throughput, p95 latency, and breaking points

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| API | FastAPI + Uvicorn |
| HTTP client | httpx `AsyncClient` (shared lifespan) |
| Inference | Ollama (`smollm2:135m` by default) |
| Tests | pytest |
| Load tests | Locust |

---

## Requirements

- Python 3.12+
- [Ollama](https://ollama.com/) running locally with the target model pulled
- Dependencies from `requirements.txt`

## Setup

```bash
# Optional: create a virtualenv first
pip install -r requirements.txt

cp .env.example .env
# Edit .env if Ollama is not on 127.0.0.1:11434
```

Pull the model (once):

```bash
ollama pull smollm2:135m
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

### API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Gateway + Ollama readiness |
| `POST` | `/generate` | `{ "prompt": "..." }` → `{ "response": "..." }` (prompt 1–500 chars) |

PowerShell example:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/generate" `
  -Method Post -ContentType "application/json" `
  -Body '{"prompt": "Say hello in one sentence."}'
```

### Docker

```bash
docker build -t llm-api-gateway .
docker run --rm -p 8000:8000 --env-file .env llm-api-gateway
```

The container must reach Ollama (set `OLLAMA_BASE_URL`, e.g. `http://host.docker.internal:11434` on Docker Desktop).

### Tests & load

```bash
pytest tests/ -v
locust -f load_tests/locustfile.py --host http://localhost:8000
```

---

## Performance & Benchmarks

### Test environment

- **Model:** `smollm2:135m` (via Ollama)
- **CPU:** AMD Ryzen 5500U with Radeon Graphics
- **RAM:** 32GB DDR4

### Results

- **Optimal capacity:** 1–2 concurrent users (~0.9 RPS, p95 &lt; 7s, 0% failure)
- **Soft limit:** 5+ concurrent users (~1.6 RPS, p95 ~28s, 0% failure)
- **Hard breaking point:** 8+ concurrent users (queue timeouts)

---

## Configuration

See [`.env.example`](.env.example) for `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and timeout knobs.
"# llm-api-with-test-harness-main" 
