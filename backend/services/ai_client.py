import httpx
from backend.config import get_settings

_OPENAI_MODEL = "gpt-4o-mini"
_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


async def complete(prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    text, _ = await complete_with_usage(prompt, system=system, max_tokens=max_tokens)
    return text


async def complete_with_usage(
    prompt: str, system: str = "", max_tokens: int = 1000
) -> tuple[str, dict]:
    """
    Call the configured AI provider and return (text, usage_dict).
    usage_dict keys: provider, model, input_tokens, output_tokens.
    Token counts are real when the provider returns them; estimated otherwise.
    """
    settings = get_settings()
    if settings.ai_provider == "anthropic":
        return await _anthropic_with_usage(system, prompt, max_tokens, settings.anthropic_api_key)
    else:
        return await _openai_with_usage(system, prompt, max_tokens, settings.openai_api_key)


async def _openai_with_usage(
    system: str, prompt: str, max_tokens: int, api_key: str
) -> tuple[str, dict]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": _OPENAI_MODEL, "messages": messages, "max_tokens": max_tokens},
        )
        response.raise_for_status()
        data = response.json()

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return text, {
        "provider": "openai",
        "model": _OPENAI_MODEL,
        "input_tokens": usage.get("prompt_tokens") or max(1, len(str(messages)) // 4),
        "output_tokens": usage.get("completion_tokens") or max(1, len(text) // 4),
    }


async def _anthropic_with_usage(
    system: str, prompt: str, max_tokens: int, api_key: str
) -> tuple[str, dict]:
    payload: dict = {
        "model": _ANTHROPIC_MODEL,
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
    return text, {
        "provider": "anthropic",
        "model": _ANTHROPIC_MODEL,
        "input_tokens": usage.get("input_tokens") or max(1, len(prompt) // 4),
        "output_tokens": usage.get("output_tokens") or max(1, len(text) // 4),
    }
