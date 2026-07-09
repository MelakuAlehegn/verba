"""One error shape for the whole API.

Every failure — a raised HTTPException, a request-validation error, or an
unexpected crash — comes back as:

    {"error": {"code": "not_found", "message": "..."}, "request_id": "..."}

so clients parse one structure and each error carries the request id for
support/debugging. Unhandled exceptions are logged (with the id) and reduced to
a generic 500 message, never leaking internals to the client.
"""

from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import get_request_id

logger = logging.getLogger("app.error")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or get_request_id()


def _code_for(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).name.lower()
    except ValueError:
        return "error"


def _envelope(
    *, status_code: int, message: str, request_id: str | None, code: str | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code or _code_for(status_code), "message": message},
            "request_id": request_id,
        },
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _envelope(status_code=exc.status_code, message=message, request_id=_request_id(request))


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    message = "Invalid request."
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
        detail = first.get("msg", message)
        message = f"{location}: {detail}" if location else detail
    return _envelope(
        status_code=422, message=message, request_id=_request_id(request), code="validation_error"
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # The id is already on the request; the middleware's contextvar may be gone
    # by the time this runs, so log with the request context explicitly.
    logger.exception("unhandled exception", extra={"path": request.url.path})
    return _envelope(
        status_code=500,
        message="Something went wrong.",
        request_id=_request_id(request),
        code="internal_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
