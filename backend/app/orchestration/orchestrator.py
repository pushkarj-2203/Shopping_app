"""
Controller agent — the execution lifecycle.

Flow per turn:
  parse(engine) → plan(planner) → stitch context(memory+RAG)
    → execute(executor) → validate(validator) → [correct & re-execute if needed]
    → persist turns + extracted memory → summarize if context too large → return.

Everything runs deterministically with no LLM (rule-based fallbacks at each step);
configuring a provider upgrades quality without changing the flow. The controller
is the only place that knows the full sequence, keeping agents decoupled.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.orchestration import prompts
from app.orchestration.agents import (
    ExecutorAgent,
    MemoryAgent,
    PlannerAgent,
    SummarizerAgent,
    ValidatorAgent,
)
from app.orchestration.memory import MemoryManager
from app.orchestration.schemas import OrchestrationResult
from app.services.engine_service import EngineService, get_engine

logger = get_logger("orchestration.controller")


def _engine_finding(engine: EngineService, query: str):
    """Deterministic factual core: the engine's honest finding for this query."""
    req = engine.parser.parse(query)
    recommended: list[dict] = []
    allowed_facts_parts: list[str] = []
    if req.confidence_score > 0.6:
        products = engine.products_in_category(req.category)
        results = engine.matcher.match(req, products)[:5] if products else []
        if results:
            top = results[0]
            finding = (
                f"Best match: {top.product.name} ({top.match_score}% fit) at "
                f"₹{top.product.price:,.0f}. Verdict: {top.verdict}. "
                f"Strengths: {', '.join(top.pros[:2]) or 'solid all-rounder'}."
            )
            recommended = [
                {"product": r.product.to_dict(), "match_score": r.match_score, "verdict": r.verdict}
                for r in results[:3]
            ]
            for r in results[:3]:
                allowed_facts_parts.append(f"{r.product.name}: ₹{r.product.price:,.0f}, verdict {r.verdict}")
            follow_ups = engine.questionnaire.generate_follow_up(req, 1)
        else:
            finding = "No products matched. Need budget and key priorities."
            follow_ups = ["What is your budget?", "Which category?"]
    else:
        finding = "Need more detail: budget, category, and what matters most."
        follow_ups = ["What is your budget?", "What features matter most?", "Any preferred brands?"]
    allowed_facts = finding + " | " + " | ".join(allowed_facts_parts)
    structured = req.to_dict() if req.confidence_score > 0.3 else None
    return finding, recommended, follow_ups, structured, req, allowed_facts


class Orchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.memory = MemoryManager(db)
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.validator = ValidatorAgent()
        self.memory_agent = MemoryAgent()
        self.summarizer = SummarizerAgent()

    async def run(self, *, query: str, session_id: str | None, user_id: str | None) -> OrchestrationResult:
        trace_id = uuid.uuid4().hex[:12]
        engine = get_engine()
        session = await self.memory.get_or_create_session(session_id, user_id)

        finding, recommended, follow_ups, structured, req, allowed_facts = _engine_finding(engine, query)

        plan = await self.planner.run(
            query=query, engine_category=req.category, engine_confidence=req.confidence_score,
            db=self.db, session_id=session.id, trace_id=trace_id,
        )

        ctx = await self.memory.build_context(session=session, query=query)
        mem_layer = prompts.memory_layer(
            rolling_summary=ctx.rolling_summary, facts=ctx.facts, rag_snippets=ctx.rag_snippets
        )

        draft, source = await self.executor.run(
            query=query, engine_finding=finding, memory_layer=mem_layer,
            complexity=plan.complexity, db=self.db, session_id=session.id, trace_id=trace_id,
        )

        # Validate (anti-hallucination). One correction pass if issues found.
        validation = await self.validator.run(
            query=query, draft=draft, allowed_facts=allowed_facts,
            db=self.db, session_id=session.id, trace_id=trace_id,
        )
        if not validation.ok:
            logger.info("validator flagged issues, correcting: %s", validation.issues)
            draft, source = await self.executor.run(
                query=query, engine_finding=finding, memory_layer=mem_layer,
                complexity=plan.complexity, db=self.db, session_id=session.id, trace_id=trace_id,
                correction=validation.issues,
            )
            # Re-validate; if still bad, fall back to the engine's own factual text.
            recheck = await self.validator.run(
                query=query, draft=draft, allowed_facts=allowed_facts,
                db=self.db, session_id=session.id, trace_id=trace_id,
            )
            if not recheck.ok:
                draft, source = finding, "rule_based"
                validation = recheck

        # Persist conversation + extracted memory.
        await self.memory.record_turn(session.id, user_id, "user", query)
        await self.memory.record_turn(session.id, user_id, "assistant", draft)
        for kind, content, importance in await self.memory_agent.run(requirement=structured):
            await self.memory.remember(
                kind=kind, content=content, user_id=user_id, session_id=session.id, importance=importance
            )

        session.turn_count += 1

        # Compress context if it has grown past threshold (keeps future turns cheap + resumable).
        summarized = False
        if self.memory.needs_summarization(ctx):
            transcript = self.memory.transcript_for_summary(ctx)
            new_summary = await self.summarizer.run(
                transcript=transcript, db=self.db, session_id=session.id, trace_id=trace_id
            )
            await self.memory.apply_summary(session, new_summary)
            summarized = True

        return OrchestrationResult(
            response=draft, session_id=session.id, answer_source=source, trace_id=trace_id,
            structured_requirement=structured, recommended_products=recommended,
            follow_up_questions=follow_ups, plan_note=plan.note,
            validated=validation.ok, validation_issues=validation.issues, summarized=summarized,
        )
