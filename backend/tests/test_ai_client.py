from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import BaseModel

from backend.services import ai_client


class StructuredResult(BaseModel):
    summary: str
    score: int


def _settings(**overrides):
    base = {
        "ai_provider": "openai",
        "openai_api_key": "test-openai-key",
        "anthropic_api_key": "test-anthropic-key",
        "ai_live_enabled": True,
        "ai_openai_model": "gpt-test-default",
        "ai_anthropic_model": "claude-test-default",
        "ai_task_model_overrides": {},
        "ai_daily_budget_usd": 0.0,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_live_ai_disabled_by_default_blocks_provider_call(monkeypatch):
    provider = AsyncMock()
    monkeypatch.setattr(ai_client, "get_settings", lambda: _settings(ai_live_enabled=False))
    monkeypatch.setattr(ai_client, "_openai_with_usage", provider)

    with pytest.raises(ai_client.AILiveDisabledError):
        await ai_client.complete_with_usage("prompt")

    provider.assert_not_called()


@pytest.mark.asyncio
async def test_retry_behavior_for_timeout(monkeypatch):
    provider = AsyncMock(side_effect=[
        httpx.TimeoutException("timeout"),
        ("ok", {"provider": "openai", "model": "gpt-test-default", "input_tokens": 1, "output_tokens": 1}),
    ])
    sleep = AsyncMock()
    monkeypatch.setattr(ai_client, "get_settings", lambda: _settings())
    monkeypatch.setattr(ai_client, "_openai_with_usage", provider)
    monkeypatch.setattr(ai_client.asyncio, "sleep", sleep)

    text, usage = await ai_client.complete_with_usage("prompt")

    assert text == "ok"
    assert usage["provider"] == "openai"
    assert provider.await_count == 2
    sleep.assert_awaited_once()


@pytest.mark.asyncio
async def test_timeout_raises_after_retry_limit(monkeypatch):
    provider = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    monkeypatch.setattr(ai_client, "get_settings", lambda: _settings())
    monkeypatch.setattr(ai_client, "_openai_with_usage", provider)
    monkeypatch.setattr(ai_client.asyncio, "sleep", AsyncMock())

    with pytest.raises(httpx.TimeoutException):
        await ai_client.complete_with_usage(
            "prompt",
            options=ai_client.AIRequestOptions(max_retries=0),
        )

    assert provider.await_count == 1


@pytest.mark.asyncio
async def test_structured_output_success(monkeypatch):
    monkeypatch.setattr(
        ai_client,
        "complete_with_usage",
        AsyncMock(return_value=('{"summary": "parsed", "score": 7}', {"provider": "test"})),
    )

    parsed, usage = await ai_client.complete_structured_with_usage("prompt", StructuredResult)

    assert parsed == StructuredResult(summary="parsed", score=7)
    assert usage["provider"] == "test"


@pytest.mark.asyncio
async def test_structured_output_accepts_json_fence(monkeypatch):
    monkeypatch.setattr(
        ai_client,
        "complete_with_usage",
        AsyncMock(return_value=('```json\n{"summary": "parsed", "score": 7}\n```', {"provider": "test"})),
    )

    parsed, usage = await ai_client.complete_structured_with_usage("prompt", StructuredResult)

    assert parsed == StructuredResult(summary="parsed", score=7)
    assert usage["provider"] == "test"


@pytest.mark.asyncio
async def test_structured_output_accepts_generic_fence(monkeypatch):
    monkeypatch.setattr(
        ai_client,
        "complete_with_usage",
        AsyncMock(return_value=('```\n{"summary": "parsed", "score": 7}\n```', {"provider": "test"})),
    )

    parsed, usage = await ai_client.complete_structured_with_usage("prompt", StructuredResult)

    assert parsed == StructuredResult(summary="parsed", score=7)
    assert usage["provider"] == "test"


@pytest.mark.asyncio
async def test_structured_output_validation_failure(monkeypatch):
    monkeypatch.setattr(
        ai_client,
        "complete_with_usage",
        AsyncMock(return_value=('{"summary": "missing score"}', {"provider": "test"})),
    )

    with pytest.raises(ai_client.AIResponseValidationError):
        await ai_client.complete_structured_with_usage("prompt", StructuredResult)


@pytest.mark.asyncio
async def test_no_silent_json_defaulting_on_parse_failure(monkeypatch):
    monkeypatch.setattr(
        ai_client,
        "complete_with_usage",
        AsyncMock(return_value=("not json", {"provider": "test"})),
    )

    with pytest.raises(ai_client.AIResponseParseError):
        await ai_client.complete_structured_with_usage("prompt", StructuredResult)


@pytest.mark.asyncio
async def test_budget_cap_blocks_provider_call(monkeypatch):
    provider = AsyncMock()
    monkeypatch.setattr(ai_client, "get_settings", lambda: _settings(ai_daily_budget_usd=1.0))
    monkeypatch.setattr(ai_client, "_openai_with_usage", provider)

    with pytest.raises(ai_client.AIBudgetExceededError):
        await ai_client.complete_with_usage(
            "prompt",
            options=ai_client.AIRequestOptions(estimated_daily_spend_usd=1.0),
        )

    provider.assert_not_called()


@pytest.mark.asyncio
async def test_task_specific_model_override(monkeypatch):
    provider = AsyncMock(return_value=("ok", {"provider": "openai", "model": "gpt-task"}))
    monkeypatch.setattr(
        ai_client,
        "get_settings",
        lambda: _settings(ai_task_model_overrides={"brief_preview": "gpt-task"}),
    )
    monkeypatch.setattr(ai_client, "_openai_with_usage", provider)

    await ai_client.complete_with_usage("prompt", task_name="brief_preview")

    assert provider.await_args.args[4] == "gpt-task"


@pytest.mark.asyncio
async def test_cache_hit_skips_provider(monkeypatch):
    provider = AsyncMock()
    cache = AsyncMock()
    cache.get.return_value = ("cached", {"provider": "cache"})
    monkeypatch.setattr(ai_client, "get_settings", lambda: _settings())
    monkeypatch.setattr(ai_client, "_openai_with_usage", provider)

    text, usage = await ai_client.complete_with_usage(
        "prompt",
        options=ai_client.AIRequestOptions(cache_key="k", cache=cache),
    )

    assert text == "cached"
    assert usage["provider"] == "cache"
    provider.assert_not_called()
