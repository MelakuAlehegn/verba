"""Readiness: can this instance actually serve traffic *right now*?

Liveness (`/healthz`) only says the process is up. Readiness probes the
dependencies a request needs — Postgres, Qdrant, Redis — so an orchestrator
stops routing to an instance whose database or vector store is unreachable.
Each check is isolated: one dependency being down is reported per-name, not as a
crash, and the overall result is 503 unless everything is "ok".
"""

from __future__ import annotations

import logging

import redis
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.rag.vector_store import get_vector_store

logger = logging.getLogger("app.readiness")


def _check_database() -> None:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    finally:
        db.close()


def _check_qdrant() -> None:
    get_vector_store().health_check()


def _check_redis() -> None:
    client = redis.from_url(get_settings().redis_url)
    try:
        client.ping()
    finally:
        client.close()


def get_readiness() -> tuple[bool, dict[str, str]]:
    checks: dict[str, str] = {}
    # Built per-call so tests can monkeypatch the individual checks.
    for name, check in (
        ("database", _check_database),
        ("qdrant", _check_qdrant),
        ("redis", _check_redis),
    ):
        try:
            check()
            checks[name] = "ok"
        except Exception:
            logger.warning("readiness check failed: %s", name, exc_info=True)
            checks[name] = "error"
    ready = all(status == "ok" for status in checks.values())
    return ready, checks
