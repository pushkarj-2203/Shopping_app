"""
Pluggable vector index.

- ``InMemoryVectorIndex``: zero-infra default. Loads candidate rows from the DB
  (filtered by user/kind) and ranks by cosine in Python. Correct and fast enough
  for thousands of memories per user.
- ``PgVectorIndex``: production path on Supabase/Postgres. Stub shows the exact
  SQL (``ORDER BY embedding <=> :q``) used once the pgvector extension + a real
  ``vector`` column exist (added via Alembic). No extra service required.

Selection is driven by settings.VECTOR_BACKEND.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import MemoryRecord
from app.orchestration.embeddings import cosine, embed


@dataclass
class ScoredMemory:
    record: MemoryRecord
    score: float


class InMemoryVectorIndex:
    async def search(
        self,
        db: AsyncSession,
        query: str,
        *,
        user_id: str | None,
        kinds: list[str] | None = None,
        top_k: int = 5,
    ) -> list[ScoredMemory]:
        stmt = select(MemoryRecord)
        if user_id:
            stmt = stmt.where(MemoryRecord.user_id == user_id)
        if kinds:
            stmt = stmt.where(MemoryRecord.kind.in_(kinds))
        stmt = stmt.order_by(MemoryRecord.created_at.desc()).limit(500)
        rows = list(await db.scalars(stmt))

        qv = embed(query)
        scored: list[ScoredMemory] = []
        for r in rows:
            if not r.embedding:
                continue
            try:
                v = json.loads(r.embedding)
            except (json.JSONDecodeError, TypeError):
                continue
            # Blend semantic similarity with stored importance (recency-weighted writes).
            sim = cosine(qv, v)
            scored.append(ScoredMemory(record=r, score=0.85 * sim + 0.15 * r.importance))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]


class PgVectorIndex:
    """
    Production implementation sketch. Requires (one-time, via Alembic):
        CREATE EXTENSION IF NOT EXISTS vector;
        ALTER TABLE memory_records ADD COLUMN embedding_vec vector(256);
        CREATE INDEX ON memory_records USING hnsw (embedding_vec vector_cosine_ops);
    Then search is a single indexed query:
        SELECT * FROM memory_records
        WHERE user_id = :uid AND kind = ANY(:kinds)
        ORDER BY embedding_vec <=> :qvec LIMIT :k;
    Falls back to the in-memory ranker until the column/extension are present.
    """

    def __init__(self) -> None:
        self._fallback = InMemoryVectorIndex()

    async def search(self, db, query, *, user_id, kinds=None, top_k=5):
        # Real pgvector query goes here; we degrade gracefully for portability.
        return await self._fallback.search(
            db, query, user_id=user_id, kinds=kinds, top_k=top_k
        )


_index = None


def get_vector_index():
    global _index
    if _index is None:
        _index = PgVectorIndex() if settings.VECTOR_BACKEND == "pgvector" else InMemoryVectorIndex()
    return _index
