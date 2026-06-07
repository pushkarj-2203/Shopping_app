"""Price-drop alerts (UC-08). Requires authentication."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import PriceAlert, User
from app.db.session import get_db
from app.schemas.engine import AlertCreateRequest, AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = PriceAlert(
        user_id=user.id,
        product_id=body.product_id,
        product_name=body.product_name,
        target_price=body.target_price,
    )
    db.add(alert)
    await db.flush()
    return alert


@router.get("", response_model=list[AlertResponse])
async def list_alerts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(
        select(PriceAlert).where(PriceAlert.user_id == user.id).order_by(PriceAlert.created_at.desc())
    )
    return list(rows)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    alert = await db.get(PriceAlert, alert_id)
    if not alert or alert.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    await db.delete(alert)
