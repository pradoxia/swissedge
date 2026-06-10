from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from backend.config import get_settings

_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
_DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 2
_BASE_BACKOFF_SECONDS = 0.25

T = TypeVar("T", bound=BaseModel)


class AIClientError(RuntimeError):
    pass


class AILiveDisabledError(AIClientError):
    pass


class AIBudgetExceededError(AIClientError):
    pass


class AIResponseParseError(AIClientError):
    pass


class AIResponseValidationError(AIClientError):
    pass


class AIResponseCache(Protocol):
    async def get(self, key: str) -> tuple[str, dict] | None:
        ...

    async def set(self, key: str, value: tuple[str, dict]) -> None:
        ...


class NullAIResponseCache:
    async def get(self, key: str) -> tuple[str, dict] | None:
        return None

    async def set(self, key: str, value: tuple[str, dict]) -> None:
        return None


@dataclass(frozen=True)
class AIRequestOptions:
    task_name: str | None = None
    max_retries: int = _MAX_RETRIES
    base_backoff_seconds: float = _BASE_BACKOFF_SECONDS
    estimated_daily_spend_usd: float = 0.0
    cache_key: str | None = None
    cache: AIResponseCache | None = None


async def complete(prompt: str, system: str = "", max_tokens: int = 1000, task_name: str | None = None) -> str:
    text, _ = await complete_with_usage(prompt, system=system, max_tokens=max_tokens, task_name=task_name)
    return text


async def complete_with_usage(
    prompt: str,
    system: str = "",
    max_tokens: int = 1000,
    *,
    task_name: str | None = None,
    options: AIRequestOptions | None = None,
) -> tuple[str, dict]:
    """
    Call the configured AI provider and return (text, usage_dict).
    Live provider calls are disabled unless settings.ai_live_enabled is true.
    usage_dict keys include provider, model, input_tokens, output_tokens, estimated_cost.
    """
    settings = get_settings()
    request_options = options or AIRequestOptions(task_name=task_name)
    task = task_name or request_options.task_name
    _ensure_live_ai_allowed(settings)
    _check_budget(settings, request_options.estimated_daily_spend_usd)

    cache = request_options.cache
    if cache and request_options.cache_key:
        cached = await cache.get(request_options.cache_key)
        if cached is not None:
            return cached

    if settings.ai_provider == "anthropic":
        model = _model_for_task(settings.ai_anthropic_model or _DEFAULT_ANTHROPIC_MODEL, task, settings)
        result = await _with_retries(
            lambda: _anthropic_with_usage(system, prompt, max_tokens, settings.anthropic_api_key, model),
            max_retries=request_options.max_retries,
            base_backoff_seconds=request_options.base_backoff_seconds,
        )
    else:
        model = _model_for_task(settings.ai_openai_model or _DEFAULT_OPENAI_MODEL, task, settings)
        result = await _with_retries(
            lambda: _openai_with_usage(system, prompt, max_tokens, settings.openai_api_key, model),
            max_retries=request_options.max_retries,
            base_backoff_seconds=request_options.base_backoff_seconds,
        )

    if cache and request_options.cache_key:
        await cache.set(request_options.cache_key, result)
    return result


async def complete_structured_with_usage(
    prompt: str,
    schema: type[T],
    system: str = "",
    max_tokens: int = 1000,
    *,
    task_name: str | None = None,
    options: AIRequestOptions | None = None,
) -> tuple[T, dict]:
    structured_system = (
        f"{system.strip()}\n\n" if system.strip() else ""
    ) + "Return only one JSON object that matches the requested schema. No markdown."
    text, usage = await complete_with_usage(
        prompt,
        system=structured_system,
        max_tokens=max_tokens,
        task_name=task_name,
        options=options,
    )
    try:
        raw = json.loads(_strip_json_fence(text))
    except json.JSONDecodeError as exc:
        raise AIResponseParseError("AI response was not valid JSON.") from exc
    try:
        return schema.model_validate(raw), usage
    except ValidationError as exc:
        raise AIResponseValidationError("AI response did not match the required schema.") from exc


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if not lines:
        return stripped
    first_line = lines[0].strip().lower()
    if first_line not in {"```", "```json"}:
        return stripped
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _ensure_live_ai_allowed(settings: Any) -> None:
    if not getattr(settings, "ai_live_enabled", False):
        raise AILiveDisabledError("Live AI is disabled. Dani approval is required before provider calls.")


def _check_budget(settings: Any, estimated_daily_spend_usd: float) -> None:
    cap = float(getattr(settings, "ai_daily_budget_usd", 0.0) or 0.0)
    if cap > 0 and estimated_daily_spend_usd >= cap:
        raise AIBudgetExceededError("AI daily budget cap would be exceeded.")


def _model_for_task(default_model: str, task_name: str | None, settings: Any) -> str:
    overrides = getattr(settings, "ai_task_model_overrides", {}) or {}
    if task_name and isinstance(overrides, dict):
        override = overrides.get(task_name)
        if isinstance(override, str) and override.strip():
            return override.strip()
    return default_model


async def _with_retries(call, *, max_retries: int, base_backoff_seconds: float) -> tuple[str, dict]:
    attempts = max_retries + 1
    for attempt in range(attempts):
        try:
            return await call()
        except Exception as exc:
            if attempt >= max_retries or not _is_retryable(exc):
                raise
            await asyncio.sleep(base_backoff_seconds * (2 ** attempt))
    raise AIClientError("AI request retry loop exited unexpectedly.")


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS_CODES
    return False


async def _openai_with_usage(
    system: str, prompt: str, max_tokens: int, api_key: str, model: str
) -> tuple[str, dict]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages, "max_tokens": max_tokens},
        )
        response.raise_for_status()
        data = response.json()

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return text, _usage(
        provider="openai",
        model=model,
        input_tokens=usage.get("prompt_tokens") or max(1, len(str(messages)) // 4),
        output_tokens=usage.get("completion_tokens") or max(1, len(text) // 4),
    )


async def _anthropic_with_usage(
    system: str, prompt: str, max_tokens: int, api_key: str, model: str
) -> tuple[str, dict]:
    payload: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    text = data["content"][0]["text"]
    usage = data.get("usage", {})
    return text, _usage(
        provider="anthropic",
        model=model,
        input_tokens=usage.get("input_tokens") or max(1, len(prompt) // 4),
        output_tokens=usage.get("output_tokens") or max(1, len(text) // 4),
    )


def _usage(*, provider: str, model: str, input_tokens: int, output_tokens: int) -> dict:
    total_tokens = int(input_tokens or 0) + int(output_tokens or 0)
    return {
        "provider": provider,
        "model": model,
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "total_tokens": total_tokens,
        "estimated_cost": _estimate_cost(provider, model, input_tokens, output_tokens),
    }


def _estimate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    # Conservative placeholder until pricing is explicitly configured.
    return 0.0
