"""Per-request correlation id + access logging.

A pure-ASGI middleware assigns each request an id (honoring an inbound
`X-Request-ID` from a proxy, else a fresh uuid), stashes it in a contextvar so
every log line emitted while handling the request carries it, echoes it back on
the response, and logs one structured start/end line with method, path, status,
and duration. Pure ASGI (not BaseHTTPMiddleware) so the contextvar set here is
visible to the endpoint — they run in the same coroutine.
"""

from __future__ import annotations

import contextvars
import logging
import time
from uuid import uuid4

logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "x-request-id"

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str | None) -> None:
    _request_id.set(value)


class RequestContextMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        inbound = headers.get(REQUEST_ID_HEADER.encode())
        request_id = inbound.decode() if inbound else str(uuid4())
        token = _request_id.set(request_id)
        # Also stash on scope state so exception handlers can read it even when
        # the 500 handler runs outside this middleware's contextvar scope.
        scope.setdefault("state", {})["request_id"] = request_id

        method = scope.get("method")
        path = scope.get("path")
        started = time.perf_counter()
        status_code: dict[str, int | None] = {"value": None}

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                status_code["value"] = message["status"]
                message.setdefault("headers", []).append(
                    (REQUEST_ID_HEADER.encode(), request_id.encode())
                )
            await send(message)

        def _elapsed_ms() -> float:
            return round((time.perf_counter() - started) * 1000, 1)

        logger.info("request.start", extra={"method": method, "path": path})
        try:
            await self.app(scope, receive, send_wrapper)
            logger.info(
                "request.end",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": status_code["value"],
                    "duration_ms": _elapsed_ms(),
                },
            )
        except Exception:
            logger.exception(
                "request.error",
                extra={"method": method, "path": path, "duration_ms": _elapsed_ms()},
            )
            raise
        finally:
            _request_id.reset(token)
