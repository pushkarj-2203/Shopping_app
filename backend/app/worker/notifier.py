"""
Pluggable notification sink for triggered alerts.

Default ``log`` notifier just records the event (zero cost, zero config). Swap to
email/WhatsApp/push by implementing ``Notifier.send`` and selecting it in
``get_notifier``. Kept separate so the job logic never hard-codes a channel.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger("worker.notifier")


class LogNotifier:
    async def send(self, *, user_id: str | None, title: str, message: str) -> None:
        logger.info("ALERT → user=%s | %s | %s", user_id, title, message)


def get_notifier():
    # Future: branch on settings.NOTIFIER (email/whatsapp/push).
    return LogNotifier()
