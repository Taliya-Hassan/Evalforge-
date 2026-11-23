"""LLM provider adapters. `generate(model, prompt)` returns the model's text answer."""

import httpx

from app.config import settings
from app.models import Model

TIMEOUT = 60.0
ALLOWED_PARAMS = ("temperature", "max_tokens")


class ProviderError(Exception):
    pass


def _mock(model: Model, prompt: str) -> str:
    """Deterministic fake model. params = {"responses": {"<prompt>": "<answer>"}}."""
    responses = (model.params or {}).get("responses", {})
    if prompt in responses:
        return str(responses[prompt])
    return f"Mock answer to: {prompt}"


def _openai(model: Model, prompt: str) -> str:
    if not settings.openai_api_key:
        raise ProviderError("OPENAI_API_KEY is not set")
    body = {"model": model.model_identifier, "messages": [{"role": "user", "content": prompt}]}
    body.update({k: v for k, v in (model.params or {}).items() if k in ALLOWED_PARAMS})
    r = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json=body,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"] or ""


def _anthropic(model: Model, prompt: str) -> str:
    if not settings.anthropic_api_key:
        raise ProviderError("ANTHROPIC_API_KEY is not set")
    params = model.params or {}
    body = {
        "model": model.model_identifier,
        "max_tokens": params.get("max_tokens", 1024),
        "messages": [{"role": "user", "content": prompt}],
    }
    if "temperature" in params:
        body["temperature"] = params["temperature"]
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        },
        json=body,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")


PROVIDERS = {"mock": _mock, "openai": _openai, "anthropic": _anthropic}


def generate(model: Model, prompt: str) -> str:
    fn = PROVIDERS.get(model.provider)
    if fn is None:
        raise ProviderError(f"Unknown provider: {model.provider}")
    return fn(model, prompt)
