"""
Modular agents. Each agent is small, single-purpose, and **degrades to a
deterministic rule-based path** when no LLM provider is configured — so the
entire pipeline runs at $0 and is fully testable offline.

Agents:
  PlannerAgent     — classify intent/category, decide what intelligence is needed.
  ExecutorAgent    — turn the engine's factual finding into the user-facing reply.
  MemoryAgent      — extract durable facts/episodes worth persisting.
  ValidatorAgent   — fact-check the draft against allowed facts (anti-hallucination).
  SummarizerAgent  — compress transcript into a rolling summary.
  (ControllerAgent — the orchestrator itself; see orchestrator.py.)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestration import prompts, runtime


@dataclass
class Plan:
    category: str | None
    needs_clarification: bool
    complexity: float
    note: str = ""


@dataclass
class Validation:
    ok: bool
    issues: list[str] = field(default_factory=list)


class PlannerAgent:
    """Rule-based intent/category classification; LLM only escalates ambiguity."""

    async def run(self, *, query: str, engine_category: str, engine_confidence: float,
                  db: AsyncSession, session_id: str, trace_id: str) -> Plan:
        complexity = 1.0 - max(0.0, min(1.0, engine_confidence))
        needs_clarification = engine_confidence < 0.4
        plan = Plan(
            category=None if engine_category == "unknown" else engine_category,
            needs_clarification=needs_clarification,
            complexity=complexity,
            note="rule_based",
        )
        # If ambiguous and an LLM is available, ask it for a tie-break plan (deep tier).
        if needs_clarification:
            c = await runtime.invoke(
                agent="planner", system=prompts.SYSTEM, prompt=prompts.planner_task(query),
                complexity=complexity, db=db, session_id=session_id, trace_id=trace_id,
            )
            if c and c.text:
                plan.note = c.text.strip()[:500]
        return plan


class ExecutorAgent:
    async def run(self, *, query: str, engine_finding: str, memory_layer: str,
                  complexity: float, db: AsyncSession, session_id: str, trace_id: str,
                  correction: list[str] | None = None) -> tuple[str, str]:
        system = prompts.SYSTEM + (("\n\n" + memory_layer) if memory_layer else "")
        task = prompts.executor_task(query, engine_finding)
        if correction:
            task += "\n\n" + prompts.correction_layer(correction)
        c = await runtime.invoke(
            agent="executor", system=system, prompt=task, complexity=complexity,
            db=db, session_id=session_id, trace_id=trace_id,
        )
        if c and c.text.strip():
            return c.text.strip(), c.provider
        return engine_finding, "rule_based"  # fallback: the engine's own factual text


class ValidatorAgent:
    """Guards against hallucination. Heuristic when no LLM; LLM JSON check otherwise."""

    _PRICE_RE = re.compile(r"₹\s?[\d,]+")

    async def run(self, *, query: str, draft: str, allowed_facts: str,
                  db: AsyncSession, session_id: str, trace_id: str) -> Validation:
        # Heuristic guard (always runs, even with LLM): any ₹ price in the draft
        # must appear in the allowed facts.
        issues: list[str] = []
        for price in self._PRICE_RE.findall(draft):
            norm = price.replace(" ", "")
            if norm not in allowed_facts.replace(" ", ""):
                issues.append(f"Unsupported price in reply: {price}")
        c = await runtime.invoke(
            agent="validator", system=prompts.SYSTEM,
            prompt=prompts.validator_task(query, draft, allowed_facts),
            db=db, session_id=session_id, trace_id=trace_id,
        )
        if c and c.text:
            try:
                parsed = json.loads(_extract_json(c.text))
                if not parsed.get("ok", True):
                    issues.extend(parsed.get("issues", []))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return Validation(ok=len(issues) == 0, issues=issues)


class MemoryAgent:
    """Extracts durable facts/episodes from a turn. Rule-based extraction by default."""

    async def run(self, *, requirement: dict | None) -> list[tuple[str, str, float]]:
        # returns list of (kind, content, importance)
        out: list[tuple[str, str, float]] = []
        if not requirement:
            return out
        budget = requirement.get("budget_range", [0, 0])
        if budget and budget[1] not in (0, None) and budget[1] != float("inf"):
            out.append(("fact", f"User's budget ceiling is ~₹{int(budget[1]):,}.", 0.8))
        if requirement.get("priorities"):
            out.append(("fact", f"User prioritizes: {', '.join(requirement['priorities'])}.", 0.7))
        if requirement.get("avoided_brands"):
            out.append(("fact", f"User avoids brands: {', '.join(requirement['avoided_brands'])}.", 0.75))
        if requirement.get("use_cases"):
            out.append(("episodic", f"Use case mentioned: {', '.join(requirement['use_cases'])}.", 0.5))
        return out


class SummarizerAgent:
    async def run(self, *, transcript: str, db: AsyncSession, session_id: str,
                  trace_id: str) -> str:
        c = await runtime.invoke(
            agent="summarizer", system=prompts.SYSTEM,
            prompt=prompts.summarizer_task(transcript), db=db, session_id=session_id, trace_id=trace_id,
        )
        if c and c.text.strip():
            return c.text.strip()
        return _extractive_summary(transcript)  # deterministic fallback


# ---------- helpers ----------
def _extract_json(text: str) -> str:
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if start != -1 and end != -1 else "{}"


def _extractive_summary(transcript: str, max_chars: int = 600) -> str:
    """Zero-cost fallback summary: keep the most informative lines."""
    lines = [l.strip() for l in transcript.splitlines() if l.strip()]
    # Prefer lines mentioning decisions, budgets, verdicts, products.
    key = re.compile(r"(budget|₹|buy|wait|don't|skip|verdict|prioriti|avoid|match)", re.I)
    ranked = sorted(lines, key=lambda l: (bool(key.search(l)), len(l)), reverse=True)
    out, total = [], 0
    for l in ranked:
        if total + len(l) > max_chars:
            break
        out.append(l)
        total += len(l)
    return " ".join(out) if out else transcript[:max_chars]
