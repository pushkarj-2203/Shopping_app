"""
APScheduler-based worker process.

Runs autonomous jobs on a cron cadence in a process separate from the API, so
heavy sweeps never block request latency and can be scaled independently. Each
job gets its own DB session. Schedules are config-light and obvious; move to a
distributed scheduler (or n8n triggering the /internal endpoints) at scale.
"""

from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal, init_db
from app.worker import jobs

logger = get_logger("worker")


async def _run(job):
    async with SessionLocal() as db:
        try:
            await job(db)
        except Exception:  # noqa: BLE001
            logger.exception("job %s failed", getattr(job, "__name__", job))


async def main() -> None:
    configure_logging()
    await init_db()
    sched = AsyncIOScheduler()
    # UC-08: price sweep every 6 hours (tune via ops). Memory upkeep daily.
    sched.add_job(lambda: asyncio.create_task(_run(jobs.price_alert_sweep)),
                  IntervalTrigger(hours=6), id="price_alert_sweep", next_run_time=None)
    sched.add_job(lambda: asyncio.create_task(_run(jobs.memory_maintenance)),
                  IntervalTrigger(hours=24), id="memory_maintenance")
    sched.start()
    logger.info("Worker started: price_alert_sweep(6h), memory_maintenance(24h)")
    # Run one sweep immediately on boot, then idle.
    await _run(jobs.price_alert_sweep)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
