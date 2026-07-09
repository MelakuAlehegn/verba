"""Redis-backed fixed-window rate limiting.

A shared counter in Redis (INCR + EXPIRE) so the limit holds across every API
instance — an in-process counter would multiply by the worker count and reset on
restart. Keyed by client IP as a first line of defense against floods/abuse.

Fail-open by design: if Redis is unreachable the request is allowed (a limiter
outage must not take down the API). Health probes are never limited.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

import redis
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.request_context import get_request_id

logger = logging.getLogger("app.ratelimit")

_SKIP_SUFFIXES = ("/healthz", "/readyz")


class RateLimiter(Protocol):
    def hit(self, key: str) -> tuple[bool, int]:
        """Register one request for `key`; return (allowed, retry_after_seconds)."""
        ...


class RedisRateLimiter:
    def __init__(self, client: redis.Redis, *, limit: int, window_seconds: int) -> None:
        self._client = client
        self._limit = limit
        self._window = window_seconds

    def hit(self, key: str) -> tuple[bool, int]:
        redis_key = f"ratelimit:{key}"
        try:
            count = self._client.incr(redis_key)
            if count == 1:
                # First hit in this window starts the countdown to reset.
                self._client.expire(redis_key, self._window)
            if count > self._limit:
                ttl = self._client.ttl(redis_key)
                return False, max(int(ttl), 1)
            return True, 0
        except Exception:
            logger.warning("rate limiter unavailable; allowing request", exc_info=True)
            return True, 0  # fail-open


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    client = redis.from_url(settings.redis_url)
    return RedisRateLimiter(
        client,
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


def _client_ip(scope, headers: dict[bytes, bytes]) -> str:
    forwarded = headers.get(b"x-forwarded-for")
    if forwarded:
        # First hop is the original client (proxies append on the right).
        return forwarded.decode().split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    def __init__(self, app, limiter: RateLimiter | None = None) -> None:
        self.app = app
        self._limiter = limiter

    @property
    def limiter(self) -> RateLimiter:
        return self._limiter or get_rate_limiter()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope.get("path", "").endswith(_SKIP_SUFFIXES):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        allowed, retry_after = self.limiter.hit(_client_ip(scope, headers))
        if allowed:
            await self.app(scope, receive, send)
            return

        response = JSONResponse(
            status_code=429,
            content={
                "error": {"code": "rate_limited", "message": "Too many requests."},
                "request_id": get_request_id(),
            },
            headers={"Retry-After": str(retry_after)},
        )
        await response(scope, receive, send)
