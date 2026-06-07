"""
Async cache abstraction.

Uses Redis when ``REDIS_URL`` is configured; otherwise falls back to a simple
in-process TTL dict so the app runs with zero external dependencies in dev.

The cache is the backbone of AI cost control: price/review intelligence and
LLM responses are cached for ``CACHE_TTL_SECONDS`` (24h by default), and atomic
counters here enforce per-user and global usage budgets.
"""

from __future__ import annotations

import time
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class _InMemoryCache:
    """Minimal TTL cache + atomic counters. Single-process only."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}
        self._counters: dict[str, tuple[float, int]] = {}

    async def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        expires, value = item
        if expires and expires < time.time():
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expires = time.time() + ttl if ttl else 0
        self._store[key] = (expires, value)

    async def incr(self, key: str, ttl: int) -> int:
        now = time.time()
        expires, count = self._counters.get(key, (now + ttl, 0))
        if expires < now:
            expires, count = now + ttl, 0
        count += 1
        self._counters[key] = (expires, count)
        return count

    async def ping(self) -> bool:
        return True


class _RedisCache:
    def __init__(self, url: str) -> None:
        import redis.asyncio as redis  # imported lazily so redis is optional

        self._r = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._r.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self._r.set(key, value, ex=ttl or None)

    async def incr(self, key: str, ttl: int) -> int:
        count = await self._r.incr(key)
        if count == 1:
            await self._r.expire(key, ttl)
        return count

    async def ping(self) -> bool:
        try:
            return bool(await self._r.ping())
        except Exception:  # noqa: BLE001
            return False


_cache: _InMemoryCache | _RedisCache | None = None


def get_cache():
    global _cache
    if _cache is None:
        if settings.REDIS_URL:
            try:
                _cache = _RedisCache(settings.REDIS_URL)
                logger.info("Cache backend: Redis")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Redis init failed (%s); using in-memory cache", exc)
                _cache = _InMemoryCache()
        else:
            _cache = _InMemoryCache()
            logger.info("Cache backend: in-memory")
    return _cache
