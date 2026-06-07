"""
LLM invocation runtime: routing + retry + fallback + tracing.

Every agent LLM call goes through ``invoke``. It:
  1. routes to a model/max_tokens tier (router),
  2. retries transient provider errors with exponential backoff,
  3. logs an LLMCallLog row (observability + cost),
  4. returns ``None`` when the provider is disabled or all attempts fail — the
     caller (agent) then uses its deterministic rule-based fallback.

This is the single choke point where reliability and cost are enforced.
"""

from __future__ import annotations

import asyncio
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import LLMCallLog
from app.orchestration import providers
from app.orchestration.providers import Completion, ProviderDisabled, ProviderError
from app.orchestration.router import route

logger = get_logger("orchestration.runtime")


async def invoke(
    *, agent: str, system: str, prompt: str, complexity: float = 0.0,
    db: AsyncSession | None = None, session_id: str | None = None, trace_id: str | None = None,
) -> Completion | None:
    model, max_tokens = route(agent, complexity=complexity)
    attempts = settings.LLM_MAX_RETRIES + 1
    outcome = "ok"
    start = perf_counter()
    result: Completion | None = None

    for attempt in range(attempts):
        try:
            result = await providers.complete(
                system=system, prompt=prompt, model=model, max_tokens=max_tokens
            )
            outcome = "ok" if attempt == 0 else "retry"
            break
        except ProviderDisabled:
            outcome = "fallback"
            break
        except ProviderError as exc:
            logger.warning("agent=%s attempt=%d failed: %s", agent, attempt + 1, exc)
            outcome = "error"
            if attempt < attempts - 1:
                await asyncio.sleep(settings.LLM_RETRY_BASE_DELAY * (2 ** attempt))

    latency = (perf_counter() - start) * 1000
    if db is not None:
        try:
            db.add(LLMCallLog(
                session_id=session_id, agent=agent, provider=result.provider if result else settings.LLM_PROVIDER,
                model=model, prompt_tokens=result.prompt_tokens if result else 0,
                completion_tokens=result.completion_tokens if result else 0,
                latency_ms=round(latency, 1), outcome=outcome, trace_id=trace_id,
            ))
        except Exception:  # noqa: BLE001 — never let logging break the request
            pass
    return result
