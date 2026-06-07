"""
Autonomous background jobs.

price_alert_sweep — UC-08: for every active alert, look up the current price and,
if it has dropped to/below the user's target, mark the alert triggered and notify.
Idempotent (won't re-trigger an already-triggered alert) and safe to run frequently.

The price lookup is injected (``price_lookup``) so the job is testable offline and
can use the seeded catalog, the data provider, or a real price API interchangeably.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import PriceAlert
from app.worker.notifier import get_notifier

logger = get_logger("worker.jobs")

PriceLookup = Callable[[str], Awaitable[float | None]]


async def default_price_lookup(product_id: str) -> float | None:
    """Resolve current price from the seeded catalog (swap for a live API/provider)."""
    from app.services.engine_service import get_engine

    product = get_engine().products.get(product_id)
    return product.price if product else None


async def price_alert_sweep(db: AsyncSession, price_lookup: PriceLookup = default_price_lookup) -> dict:
    notifier = get_notifier()
    alerts = list(await db.scalars(select(PriceAlert).where(PriceAlert.is_active.is_(True))))
    checked = triggered = 0

    for alert in alerts:
        checked += 1
        price = await price_lookup(alert.product_id)
        if price is None:
            continue
        alert.last_seen_price = price
        if price <= alert.target_price and alert.triggered_at is None:
            alert.triggered_at = datetime.now(timezone.utc)
            alert.is_active = False
            triggered += 1
            await notifier.send(
                user_id=alert.user_id,
                title=f"Price drop: {alert.product_name}",
                message=(
                    f"{alert.product_name} hit ₹{price:,.0f} "
                    f"(your target ₹{alert.target_price:,.0f}). Good time to buy."
                ),
            )
    await db.commit()
    result = {"checked": checked, "triggered": triggered}
    logger.info("price_alert_sweep %s", result)
    return result


async def memory_maintenance(db: AsyncSession, max_working_per_session: int = 200) -> dict:
    """Housekeeping: prune oldest 'working' memories beyond a cap (keeps RAG lean)."""
    from app.db.models import MemoryRecord

    rows = list(await db.scalars(
        select(MemoryRecord).where(MemoryRecord.kind == "working").order_by(MemoryRecord.created_at.desc())
    ))
    pruned = 0
    for r in rows[max_working_per_session:]:
        await db.delete(r)
        pruned += 1
    await db.commit()
    return {"pruned_working_memories": pruned}
