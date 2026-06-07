"""
Memory architecture — four tiers + context stitching + resumable sessions.

Tiers (all rows live in ``memory_records``, distinguished by ``kind``):
  • working  — recent turns kept verbatim (short-term scratch).
  • episodic — durable events/decisions ("rejected iPhone: over budget").
  • summary  — compressed rolling summary of older turns.
  • fact     — stable long-term user facts/preferences.

Context stitching (build_context): rolling summary + top-K RAG over episodic/fact
memory + the last N verbatim turns, all kept under MAX_CONTEXT_TOKENS. Because the
summary + facts are persisted on the session row and in memory_records, a session
can be **resumed after any token/context reset**: we reload the summary, re-run RAG,
and continue — no transcript replay needed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ChatMessage, MemoryRecord, OrchestrationSession
from app.orchestration.embeddings import embed
from app.orchestration.providers import estimate_tokens
from app.orchestration.vector import get_vector_index


@dataclass
class AssembledContext:
    rolling_summary: str = ""
    facts: list[str] = field(default_factory=list)
    rag_snippets: list[str] = field(default_factory=list)
    recent_turns: list[tuple[str, str]] = field(default_factory=list)  # (role, content)
    token_estimate: int = 0


class MemoryManager:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.vector = get_vector_index()

    # ---------- session lifecycle ----------
    async def get_or_create_session(
        self, session_id: str | None, user_id: str | None
    ) -> OrchestrationSession:
        if session_id:
            existing = await self.db.get(OrchestrationSession, session_id)
            if existing:
                return existing
        sess = OrchestrationSession(user_id=user_id)
        if session_id:
            sess.id = session_id
        self.db.add(sess)
        await self.db.flush()
        return sess

    # ---------- writes ----------
    async def remember(
        self, *, kind: str, content: str, user_id: str | None, session_id: str | None,
        importance: float = 0.5, meta: dict | None = None,
    ) -> MemoryRecord:
        rec = MemoryRecord(
            kind=kind, content=content, user_id=user_id, session_id=session_id,
            importance=importance, embedding=json.dumps(embed(content)),
            meta=json.dumps(meta) if meta else None,
        )
        self.db.add(rec)
        await self.db.flush()
        return rec

    async def record_turn(self, session_id: str, user_id: str | None, role: str, content: str) -> None:
        self.db.add(ChatMessage(session_id=session_id, user_id=user_id, role=role, content=content))

    # ---------- reads / stitching ----------
    async def _recent_turns(self, session_id: str, limit: int) -> list[tuple[str, str]]:
        rows = list(await self.db.scalars(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc()).limit(limit)
        ))
        return [(r.role, r.content) for r in reversed(rows)]

    async def build_context(
        self, *, session: OrchestrationSession, query: str
    ) -> AssembledContext:
        ctx = AssembledContext(rolling_summary=session.rolling_summary or "")

        # Long-term facts (always injected; cheap and high-signal).
        fact_rows = list(await self.db.scalars(
            select(MemoryRecord).where(
                MemoryRecord.user_id == session.user_id, MemoryRecord.kind == "fact"
            ).order_by(MemoryRecord.created_at.desc()).limit(20)
        )) if session.user_id else []
        ctx.facts = [r.content for r in fact_rows]

        # RAG over episodic + fact memory.
        scored = await self.vector.search(
            self.db, query, user_id=session.user_id,
            kinds=["episodic", "fact"], top_k=settings.RAG_TOP_K,
        )
        ctx.rag_snippets = [s.record.content for s in scored if s.score > 0.15]

        # Recent verbatim turns.
        ctx.recent_turns = await self._recent_turns(session.id, settings.WORKING_MEMORY_TURNS)

        ctx.token_estimate = estimate_tokens(
            ctx.rolling_summary + " ".join(ctx.facts) + " ".join(ctx.rag_snippets)
            + " ".join(c for _, c in ctx.recent_turns)
        )
        return ctx

    # ---------- compression ----------
    def needs_summarization(self, ctx: AssembledContext) -> bool:
        return ctx.token_estimate > settings.SUMMARIZE_THRESHOLD_TOKENS

    async def apply_summary(self, session: OrchestrationSession, new_summary: str) -> None:
        session.rolling_summary = new_summary
        session.token_estimate = estimate_tokens(new_summary)
        session.updated_at = datetime.now(timezone.utc)
        await self.remember(
            kind="summary", content=new_summary, user_id=session.user_id,
            session_id=session.id, importance=0.7,
        )

    def transcript_for_summary(self, ctx: AssembledContext) -> str:
        prior = f"PRIOR SUMMARY: {ctx.rolling_summary}\n" if ctx.rolling_summary else ""
        turns = "\n".join(f"{role}: {content}" for role, content in ctx.recent_turns)
        return prior + turns
