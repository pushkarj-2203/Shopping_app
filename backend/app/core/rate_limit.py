"""
Dependency-based rate limiting built on the shared cache abstraction.

Why not slowapi decorators? They rewrite the endpoint signature, which breaks
FastAPI request-body parsing. A dependency is signature-safe, works with both
the Redis and in-memory cache backends (so limits are shared across instances
when Redis is configured), and reuses the same atomic counters we use for AI
cost control.

Usage:
    @router.post("/login", dependencies=[Depends(RateLimiter("10/minute"))])
"""


from fastapi import HTTPException, Request, status

from app.core.cache import get_cache

_PERIODS = {"second": 1, "minute": 60, "hour": 3600, "day": 86_400}


def _parse(limit: str) -> tuple[int, int]:
    """'10/minute' -> (10, 60)."""
    times, _, period = limit.partition("/")
    return int(times), _PERIODS.get(period.strip().rstrip("s"), 60)


def _client_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    fwd = request.headers.get("x-forwarded-for")
    ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "anon")
    return f"ip:{ip}"


class RateLimiter:
    def __init__(self, limit: str) -> None:
        self.times, self.seconds = _parse(limit)

    async def __call__(self, request: Request) -> None:
        cache = get_cache()
        bucket = f"rl:{request.url.path}:{_client_key(request)}"
        count = await cache.incr(bucket, ttl=self.seconds)
        if count > self.times:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({self.times} per {self.seconds}s). Please slow down.",
                headers={"Retry-After": str(self.seconds)},
            )
