from __future__ import annotations

import httpx

from app import config


class ProviderError(Exception):
    """Safe, user-facing LLM provider error."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


async def _post_json(url: str, *, headers: dict[str, str], payload: dict) -> dict:
    timeout = httpx.Timeout(config.LLM_TIMEOUT_SECONDS, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise ProviderError("AI provider timed out. Please try again.", status_code=504) from exc
    except httpx.HTTPError as exc:
        raise ProviderError("Could not connect to an AI provider.") from exc

    if response.status_code == 429:
        raise ProviderError("The AI provider's free or account quota is temporarily exhausted. Try again later.", status_code=429)
    if response.status_code in (401, 403):
        raise ProviderError("An AI provider rejected its API key. Check the Render environment variables.", status_code=503)
    if response.is_error:
        raise ProviderError(f"An AI provider returned an error (HTTP {response.status_code}).", status_code=502)
    try:
        return response.json()
    except ValueError as exc:
        raise ProviderError("An AI provider returned an invalid response.") from exc


async def ask_gemini(system_prompt: str, user_prompt: str) -> str:
    if not config.GOOGLE_API_KEY:
        raise ProviderError("GOOGLE_API_KEY is not configured in Render.", status_code=503)

    # Send the key in a header rather than the URL to reduce accidental exposure in logs.
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GOOGLE_MODEL}:generateContent"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1800},
    }
    data = await _post_json(
        url,
        headers={"Content-Type": "application/json", "x-goog-api-key": config.GOOGLE_API_KEY},
        payload=payload,
    )
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "\n".join(part["text"] for part in parts if isinstance(part.get("text"), str)).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Gemini returned no usable text. Check the configured model and quota.") from exc
    if not text:
        raise ProviderError("Gemini returned an empty response. Try a different model or prompt.")
    return text


async def ask_groq(system_prompt: str, user_prompt: str) -> str:
    if not config.GROQ_API_KEY:
        raise ProviderError("GROQ_API_KEY is not configured in Render.", status_code=503)

    data = await _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"},
        payload={
            "model": config.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 2400,
        },
    )
    try:
        text = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError, TypeError) as exc:
        raise ProviderError("Groq returned no usable text. Check the configured model and quota.") from exc
    if not text:
        raise ProviderError("Groq returned an empty response. Try a different model or prompt.")
    return text
