from unittest.mock import Mock

from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.core.rate_limit import RateLimitMiddleware, RedisRateLimiter

# --- RedisRateLimiter (fixed window over INCR/EXPIRE) ---


def test_first_hit_starts_the_window() -> None:
    client = Mock()
    client.incr.return_value = 1
    limiter = RedisRateLimiter(client, limit=5, window_seconds=60)

    assert limiter.hit("1.2.3.4") == (True, 0)
    client.expire.assert_called_once_with("ratelimit:1.2.3.4", 60)


def test_within_limit_is_allowed() -> None:
    client = Mock()
    client.incr.return_value = 5  # exactly at the limit
    limiter = RedisRateLimiter(client, limit=5, window_seconds=60)

    assert limiter.hit("ip") == (True, 0)


def test_over_limit_is_blocked_with_retry_after() -> None:
    client = Mock()
    client.incr.return_value = 6
    client.ttl.return_value = 30
    limiter = RedisRateLimiter(client, limit=5, window_seconds=60)

    assert limiter.hit("ip") == (False, 30)


def test_limiter_fails_open_when_redis_errors() -> None:
    client = Mock()
    client.incr.side_effect = RuntimeError("redis down")
    limiter = RedisRateLimiter(client, limit=5, window_seconds=60)

    assert limiter.hit("ip") == (True, 0)  # allowed despite the outage


# --- Middleware ---


async def _ok_app(scope, receive, send) -> None:
    await JSONResponse({"ok": True})(scope, receive, send)


class FakeLimiter:
    def __init__(self, allowed: bool, retry_after: int = 0) -> None:
        self.allowed = allowed
        self.retry_after = retry_after
        self.calls: list[str] = []

    def hit(self, key: str) -> tuple[bool, int]:
        self.calls.append(key)
        return self.allowed, self.retry_after


def test_middleware_blocks_when_over_limit() -> None:
    limiter = FakeLimiter(allowed=False, retry_after=42)
    client = TestClient(RateLimitMiddleware(_ok_app, limiter=limiter))

    response = client.get("/api/v1/chats")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "42"
    assert response.json()["error"]["code"] == "rate_limited"


def test_middleware_allows_under_limit() -> None:
    limiter = FakeLimiter(allowed=True)
    client = TestClient(RateLimitMiddleware(_ok_app, limiter=limiter))

    response = client.get("/api/v1/chats")

    assert response.status_code == 200
    assert limiter.calls  # limiter was consulted


def test_middleware_skips_health_probes() -> None:
    limiter = FakeLimiter(allowed=False)  # would block if consulted
    client = TestClient(RateLimitMiddleware(_ok_app, limiter=limiter))

    response = client.get("/api/v1/healthz")

    assert response.status_code == 200  # not rate-limited
    assert limiter.calls == []  # probe bypassed the limiter entirely
