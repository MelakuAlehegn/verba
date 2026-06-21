from __future__ import annotations

from uuid import UUID

from app.core.database import SessionLocal
from app.services.ingestion_service import ingest_document
from app.services.rag.embedding import get_embedder
from app.services.rag.vector_store import get_vector_store
from app.storage import get_storage_client
from app.workers.celery_app import celery_app


@celery_app.task(name="ingest_document")
def ingest_document_task(document_id: str) -> None:
    # The worker runs outside any web request, so it owns its DB session.
    db = SessionLocal()
    try:
        ingest_document(
            db,
            UUID(document_id),
            storage=get_storage_client(),
            embedder=get_embedder(),
            vector_store=get_vector_store(),
        )
    finally:
        db.close()


def enqueue_document_ingestion(document_id: UUID) -> None:
    """Hand off ingestion to the worker. Thin seam so the API never touches
    Celery internals (and tests can stub this out)."""
    ingest_document_task.delay(str(document_id))
