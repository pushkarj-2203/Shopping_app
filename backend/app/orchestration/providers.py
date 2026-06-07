"""
Unified LLM provider interface + token accounting.

A single ``complete()`` coroutine abstracts Anthropic, OpenAI and Ollama behind
one contract so agents and the router never branch on vendor. ``LLM_PROVIDER=none``
raises ``ProviderDisabled`` — callers (agents) catch it and use their rule-based
fallback, which is how the whole system runs at $0 with no key.

Token estimates use a 4-chars/token heuristic when a provider doesn't report usage.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


class ProviderDisabled(Exception):
    """Raised when no paid provider is configured (LLM_PROVIDER=none)."""


class ProviderError(Exception):
    """Transient provider failure; the orchestrator decides retry vs fallback."""


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class Completion:
    text: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int


async def _anthropic(system: str, prompt: str, model: str, max_tokens: int) -> Completion:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = await client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return Completion(text, "anthropic", model, resp.usage.input_tokens, resp.usage.output_tokens)


async def _openai(system: str, prompt: str, model: str, max_tokens: int) -> Completion:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    resp = await client.chat.completions.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    )
    text = resp.choices[0].message.content or ""
    u = resp.usage
    return Completion(text, "openai", model,
                      getattr(u, "prompt_tokens", 0), getattr(u, "completion_tokens", 0))


async def _ollama(system: str, prompt: str, model: str, max_tokens: int) -> Completion:
    import httpx

    async with httpx.AsyncClient(timeout=120) as http:
        r = await http.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "system": system, "prompt": prompt, "stream": False,
                  "options": {"num_predict": max_tokens}},
        )
        r.raise_for_status()
        data = r.json()
    return Completion(data.get("response", ""), "ollama", model,
                      data.get("prompt_eval_count", 0), data.get("eval_count", 0))


async def complete(*, system: str, prompt: str, model: str, max_tokens: int | None = None) -> Completion:
    provider = settings.LLM_PROVIDER
    if provider == "none":
        raise ProviderDisabled()
    mt = max_tokens or settings.LLM_MAX_TOKENS
    try:
        if provider == "anthropic":
            return await _anthropic(system, prompt, model, mt)
        if provider == "openai":
            return await _openai(system, prompt, model, mt)
        if provider == "ollama":
            return await _ollama(system, prompt, model, mt)
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(str(exc)) from exc
    raise ProviderDisabled()
