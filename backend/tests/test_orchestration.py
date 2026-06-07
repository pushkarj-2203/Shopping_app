"""Tests for the LLM orchestration layer — all run with LLM_PROVIDER=none ($0)."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("LLM_PROVIDER", "none")

import pytest

from app.orchestration.embeddings import cosine, embed
from app.orchestration.router import Tier, route


def test_local_embeddings_are_semantic():
    a = embed("phone with great camera and battery")
    b = embed("smartphone with excellent camera, good battery life")
    c = embed("washing machine front load")
    assert cosine(a, b) > cosine(a, c)  # related text is closer than unrelated


def test_router_escalates_hard_planning_to_deep():
    cheap_model, _ = route("router", complexity=0.1)
    deep_model, deep_tokens = route("planner", complexity=0.9)
    assert deep_tokens >= 1024
    # validator/summarizer always cheap tier
    assert route("validator")[1] <= 256


@pytest.mark.asyncio
async def test_orchestrator_resumable_session_and_memory():
    # Use a real async session against in-memory sqlite.
    from app.db.session import SessionLocal, init_db
    from app.orchestration import Orchestrator
    from app.services.engine_service import get_engine

    get_engine()
    await init_db()

    async with SessionLocal() as db:
        orch = Orchestrator(db)
        r1 = await orch.run(
            query="good camera phone under 70000 for photography", session_id=None, user_id="u1"
        )
        await db.commit()
        assert r1.session_id
        assert r1.answer_source == "rule_based"
        assert r1.recommended_products  # engine produced matches
        sid = r1.session_id

    # New session object (simulates a fresh request / context reset): same session id resumes.
    async with SessionLocal() as db:
        orch = Orchestrator(db)
        r2 = await orch.run(query="what about battery?", session_id=sid, user_id="u1")
        await db.commit()
        assert r2.session_id == sid  # session resumed, not recreated

    # Memory was persisted (budget fact extracted from turn 1).
    async with SessionLocal() as db:
        from sqlalchemy import select
        from app.db.models import MemoryRecord, OrchestrationSession

        facts = list(await db.scalars(
            select(MemoryRecord).where(MemoryRecord.user_id == "u1", MemoryRecord.kind == "fact")
        ))
        assert any("budget" in f.content.lower() for f in facts)
        sess = await db.get(OrchestrationSession, sid)
        assert sess is not None and sess.turn_count >= 2


@pytest.mark.asyncio
async def test_validator_blocks_unsupported_price():
    from app.orchestration.agents import ValidatorAgent

    v = ValidatorAgent()
    # Draft cites a price not present in allowed facts -> must be flagged.
    res = await v.run(
        query="q", draft="Buy it now for ₹999.",
        allowed_facts="Best match: Phone X: ₹64,999, verdict BUY",
        db=None, session_id="s", trace_id="t",
    )
    assert res.ok is False
    assert any("₹999" in i for i in res.issues)
