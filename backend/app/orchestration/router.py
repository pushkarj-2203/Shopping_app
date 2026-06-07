"""
Model routing: pick the cheapest model that can do the job.

Routing is by *task tier* (which agent, how hard the task) rather than by raw
prompt length, so cost is predictable. Planning/validation of ambiguous input
escalates to the DEEP tier; everything else stays CHEAP/STANDARD. This is where
80%+ of LLM cost is controlled before a single token is spent.
"""

from __future__ import annotations

from enum import Enum

from app.core.config import settings


class Tier(str, Enum):
    CHEAP = "cheap"
    STANDARD = "standard"
    DEEP = "deep"


# Per-agent default tier. Override-able by complexity signals (see route()).
_AGENT_TIER = {
    "router": Tier.CHEAP,
    "memory": Tier.CHEAP,
    "summarizer": Tier.CHEAP,
    "validator": Tier.CHEAP,
    "executor": Tier.STANDARD,
    "planner": Tier.STANDARD,
}


def route(agent: str, *, complexity: float = 0.0) -> tuple[str, int]:
    """Return (model, max_tokens) for an agent given a 0..1 complexity score."""
    tier = _AGENT_TIER.get(agent, Tier.STANDARD)
    # Escalate planner/executor to DEEP when the task looks genuinely hard.
    if agent in ("planner", "executor") and complexity >= 0.7:
        tier = Tier.DEEP
    model = {
        Tier.CHEAP: settings.LLM_MODEL_CHEAP,
        Tier.STANDARD: settings.LLM_MODEL_STANDARD,
        Tier.DEEP: settings.LLM_MODEL_DEEP,
    }[tier]
    max_tokens = {Tier.CHEAP: 256, Tier.STANDARD: settings.LLM_MAX_TOKENS, Tier.DEEP: 1024}[tier]
    return model, max_tokens
