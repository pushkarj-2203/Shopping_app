"""Conversational endpoint (UC-07) — routed through the multi-agent orchestrator."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.db.models import User
from app.db.session import get_db
from app.orchestration import Orchestrator
from app.schemas.engine import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(RateLimiter(settings.RATE_LIMIT_CHAT))],
)
async def chat(
    body: ChatRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    orch = Orchestrator(db)
    result = await orch.run(
        query=body.query, session_id=body.session_id, user_id=user.id if user else None
    )
    return ChatResponse(
        response=result.response,
        structured_requirement=result.structured_requirement,
        recommended_products=result.recommended_products,
        follow_up_questions=result.follow_up_questions,
        session_id=result.session_id,
        answer_source=result.answer_source,
        trace_id=result.trace_id,
        validated=result.validated,
    )
