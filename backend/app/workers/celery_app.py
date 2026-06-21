from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

# Redis is both broker (queue) and result backend. `include` registers the
# tasks module so the worker discovers ingest_document_task on startup.
celery_app = Celery(
    "document_qa_rag",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=["app.workers.tasks"],
)
