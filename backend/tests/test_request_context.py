import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter
from app.core.request_context import get_request_id, set_request_id
from app.main import create_app


def test_response_carries_a_request_id_header() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.headers.get("x-request-id")  # a generated id is echoed back


def test_inbound_request_id_is_preserved() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/healthz", headers={"X-Request-ID": "trace-123"})

    assert response.headers.get("x-request-id") == "trace-123"


def test_formatter_includes_request_id_and_extras() -> None:
    formatter = JsonFormatter()
    set_request_id("req-9")
    try:
        record = logging.LogRecord(
            name="app.request",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="request.end",
            args=(),
            exc_info=None,
        )
        record.method = "GET"
        record.path = "/api/v1/healthz"
        record.status_code = 200
        record.duration_ms = 3.2

        payload = json.loads(formatter.format(record))
    finally:
        set_request_id(None)

    assert payload["request_id"] == "req-9"
    assert payload["method"] == "GET"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 3.2


def test_request_id_absent_outside_a_request() -> None:
    set_request_id(None)
    assert get_request_id() is None
    payload = json.loads(JsonFormatter().format(logging.makeLogRecord({"msg": "x"})))
    assert "request_id" not in payload
