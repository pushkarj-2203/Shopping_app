"""Background worker tests (UC-08 price-alert sweep).

Note: tests share a process-wide in-memory DB, so assertions are scoped to each
test's own alert (by unique product_id) rather than global sweep totals.
"""

import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("LLM_PROVIDER", "none")

import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_price_alert_sweep_triggers_when_price_drops():
    from app.db.models import PriceAlert, User
    from app.db.session import SessionLocal, init_db
    from app.worker.jobs import price_alert_sweep

    await init_db()
    pid = f"prod_{uuid.uuid4().hex[:8]}"
    async with SessionLocal() as db:
        user = User(email=f"{uuid.uuid4().hex[:6]}@hunter.com", hashed_password="x")
        db.add(user)
        await db.flush()
        db.add(PriceAlert(user_id=user.id, product_id=pid,
                          product_name="Test Phone", target_price=115000))
        await db.commit()

        async def lookup(p):  # price below target only for our product
            return 114999.0 if p == pid else 999999.0

        await price_alert_sweep(db, price_lookup=lookup)
        alert = await db.scalar(select(PriceAlert).where(PriceAlert.product_id == pid))
        assert alert.triggered_at is not None
        assert alert.is_active is False
        assert alert.last_seen_price == 114999.0


@pytest.mark.asyncio
async def test_price_alert_not_triggered_above_target():
    from app.db.models import PriceAlert, User
    from app.db.session import SessionLocal, init_db
    from app.worker.jobs import price_alert_sweep

    await init_db()
    pid = f"prod_{uuid.uuid4().hex[:8]}"
    async with SessionLocal() as db:
        user = User(email=f"{uuid.uuid4().hex[:6]}@buyer.com", hashed_password="x")
        db.add(user)
        await db.flush()
        db.add(PriceAlert(user_id=user.id, product_id=pid, product_name="P", target_price=100))
        await db.commit()

        async def high(p):
            return 200.0

        await price_alert_sweep(db, price_lookup=high)
        alert = await db.scalar(select(PriceAlert).where(PriceAlert.product_id == pid))
        assert alert.triggered_at is None
        assert alert.is_active is True
