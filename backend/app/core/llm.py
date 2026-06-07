"""
Pluggable LLM layer with strict cost control.

Design goal: the product runs at **zero marginal cost by default**. The rule-based
engine answers everything; the LLM is an *optional* enhancement for phrasing the
conversational chat replies more naturally.

Cost controls (all enforced here, before any paid call is made):
  1. Provider switch — ``LLM_PROVIDER=none`` disables paid calls entirely.
  2. Response caching — identical prompts are served from cache (24h).
  3. Per-user daily call cap — ``LLM_USER_DAILY_CALL_CAP``.
  4. Global monthly token budget — ``LLM_MONTHLY_TOKEN_BUDGET``.
On any limit breach (or provider error) we fail *open* to the rule-based text,
so the user always gets an answer and the bill can never run away.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from app.core.cache import get_cache
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMResult:
    def __init__(self, text: str, source: str, tokens: int = 0):
        self.text = text
        self.source = source  # "llm" | "cache" | "rule_based"
        self.tokens = tokens


def _prompt_key(prompt: str) -> str:
    digest = hashlib.sha256(f"{settings.LLM_MODEL}:{prompt}".encode()).hexdigest()
    return f"llm:resp:{digest}"


async def _within_budget(user_id: str | None) -> tuple[bool, str]:
    cache = get_cache()
    month = datetime.now(timezone.utc).strftime("%Y%m")
    day = datetime.now(timezone.utc).strftime("%Y%m%d")

    if settings.LLM_USER_DAILY_CALL_CAP and user_id:
        calls = await cache.incr(f"llm:calls:{user_id}:{day}", ttl=86_400)
        if calls > settings.LLM_USER_DAILY_CALL_CAP:
            return False, "user_daily_cap"

    if settings.LLM_MONTHLY_TOKEN_BUDGET:
        used = await cache.get(f"llm:tokens:{month}")
        if used and int(used) >= settings.LLM_MONTHLY_TOKEN_BUDGET:
            return False, "monthly_budget"
    return True, ""


async def _record_tokens(tokens: int) -> None:
    cache = get_cache()
    month = datetime.now(timezone.utc).strftime("%Y%m")
    # incr can't add arbitrary ints on the in-memory shim; emulate with get/set.
    key = f"llm:tokens:{month}"
    used = int(await cache.get(key) or 0) + tokens
    await cache.set(key, str(used), ttl=60 * 60 * 24 * 35)


async def _call_anthropic(prompt: str, system: str) -> tuple[str, int]:
    from anthropic import AsyncAnthropic  # lazy import

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = await client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=settings.LLM_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    tokens = resp.usage.input_tokens + resp.usage.output_tokens
    return text, tokens


async def _call_ollama(prompt: str, system: str) -> tuple[str, int]:
    import httpx  # lazy import

    async with httpx.AsyncClient(timeout=60) as http:
        r = await http.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={"model": settings.LLM_MODEL, "prompt": prompt, "system": system, "stream": False},
        )
        r.raise_for_status()
        data = r.json()
    # Ollama is self-hosted (free); token accounting is best-effort.
    return data.get("response", ""), data.get("eval_count", 0)


async def enhance(
    *,
    rule_based_text: str,
    prompt: str,
    system: str = "You are PriceWise, an honest, consumer-first shopping assistant. "
    "Be concise. Never pressure the user to buy. It is fine to advise waiting or not buying.",
    user_id: str | None = None,
) -> LLMResult:
    """
    Return an LLM-polished version of ``rule_based_text`` when a provider is
    configured and budgets allow; otherwise return the rule-based text unchanged.
    """
    if settings.LLM_PROVIDER == "none":
        return LLMResult(rule_based_text, "rule_based")

    cache = get_cache()
    key = _prompt_key(prompt)
    cached = await cache.get(key)
    if cached is not None:
        return LLMResult(cached, "cache")

    ok, reason = await _within_budget(user_id)
    if not ok:
        logger.warning("LLM budget limit hit (%s); serving rule-based text", reason)
        return LLMResult(rule_based_text, "rule_based")

    try:
        if settings.LLM_PROVIDER == "anthropic":
            text, tokens = await _call_anthropic(prompt, system)
        else:  # ollama
            text, tokens = await _call_ollama(prompt, system)
    except Exception as exc:  # noqa: BLE001 — fail open, never block the user
        logger.warning("LLM call failed (%s); serving rule-based text", exc)
        return LLMResult(rule_based_text, "rule_based")

    text = text.strip() or rule_based_text
    await cache.set(key, text, ttl=settings.CACHE_TTL_SECONDS)
    await _record_tokens(tokens)
    return LLMResult(text, "llm", tokens)
