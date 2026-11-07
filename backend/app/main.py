from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app import config
from app.orchestrator import run_project_crew
from app.providers import ProviderError


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=3, max_length=config.MAX_PROMPT_CHARS)


class InMemoryRateLimiter:
    """Small single-instance guard; use an external store for multi-instance deployments."""

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - config.RATE_LIMIT_WINDOW_SECONDS
        timestamps = self._requests[key]
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if len(timestamps) >= config.RATE_LIMIT_REQUESTS:
            return False
        timestamps.append(now)
        return True


limiter = InMemoryRateLimiter()
crew_semaphore = asyncio.Semaphore(2)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title=config.APP_NAME,
    version="1.0.0",
    description="A bounded multi-agent project assistant using Gemini and Groq APIs.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "al-capilot-multi-agent"}


async def _handle_chat(request: ChatRequest, http_request: Request) -> dict[str, str]:
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Request limit reached. Please wait before trying again.")
    prompt = request.prompt.strip()
    if len(prompt) < 3:
        raise HTTPException(status_code=422, detail="Prompt must contain at least 3 non-space characters.")

    try:
        async with crew_semaphore:
            result = await run_project_crew(prompt)
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return {"response": result}


@app.post("/api/chat")
async def api_chat(request: ChatRequest, http_request: Request) -> dict[str, str]:
    return await _handle_chat(request, http_request)


@app.post("/run")
async def legacy_run(request: ChatRequest, http_request: Request) -> dict[str, str]:
    """Compatibility route used by the current GitHub Pages frontend."""
    return await _handle_chat(request, http_request)
