"""
Pluggable product-data integration.

The engine is decoupled from where products come from. By default we use the
seeded ``mock`` provider (zero cost, fully offline). Setting ``DATA_PROVIDER=google_cse``
plus the relevant API keys enables live product discovery via Google Custom Search
(free tier: 100 queries/day) — results are cached for ``CACHE_TTL_SECONDS`` to stay
within the free quota and keep cost at zero.

IMPORTANT (legal): per the usecase doc we never self-scrape Amazon/Flipkart.
Only official APIs / licensed providers are integrated here. New providers should
implement ``DataProvider.search`` and be registered in ``get_data_provider``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from app.core.cache import get_cache
from app.core.config import settings
from app.core.logging import get_logger
from app.services.engine_service import get_engine

logger = get_logger(__name__)


class DataProvider(ABC):
    @abstractmethod
    async def search(self, query: str, category: str | None = None, limit: int = 10) -> list[dict]:
        """Return a list of product dicts matching the query."""


class MockProvider(DataProvider):
    """Serves the in-memory seeded catalog. Deterministic and free."""

    async def search(self, query: str, category: str | None = None, limit: int = 10) -> list[dict]:
        engine = get_engine()
        products = (
            engine.products_in_category(category) if category else list(engine.products.values())
        )
        q = query.lower()
        ranked = sorted(
            products,
            key=lambda p: (q in p.name.lower()) or (q in p.brand.lower()),
            reverse=True,
        )
        return [p.to_dict() for p in ranked[:limit]]


class GoogleCSEProvider(DataProvider):
    """Live product discovery via Google Custom Search JSON API (free tier)."""

    async def search(self, query: str, category: str | None = None, limit: int = 10) -> list[dict]:
        if not (settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_ENGINE_ID):
            logger.warning("Google CSE keys missing; falling back to mock provider")
            return await MockProvider().search(query, category, limit)

        cache = get_cache()
        cache_key = f"cse:{category}:{query}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return json.loads(cached)

        import httpx  # lazy import

        params = {
            "key": settings.GOOGLE_CSE_API_KEY,
            "cx": settings.GOOGLE_CSE_ENGINE_ID,
            "q": f"{query} {category or ''} price india".strip(),
            "num": min(limit, 10),
        }
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                r = await http.get("https://www.googleapis.com/customsearch/v1", params=params)
                r.raise_for_status()
                items = r.json().get("items", [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google CSE failed (%s); falling back to mock", exc)
            return await MockProvider().search(query, category, limit)

        results = [
            {
                "id": it.get("cacheId") or it.get("link", ""),
                "name": it.get("title", ""),
                "link": it.get("link", ""),
                "snippet": it.get("snippet", ""),
                "category": category or "unknown",
                "source": "google_cse",
            }
            for it in items
        ]
        # Cache to respect the free-tier quota (cost control).
        await cache.set(cache_key, json.dumps(results), ttl=settings.CACHE_TTL_SECONDS)
        return results


def get_data_provider() -> DataProvider:
    if settings.DATA_PROVIDER == "google_cse":
        return GoogleCSEProvider()
    return MockProvider()
