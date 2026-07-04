"""One-off: purge chunks + Qdrant vectors left behind by soft-deleted documents.

Deletions made before the vector+chunk cleanup fix only flipped the document row
to `deleted`, leaving its chunks in Postgres and its points in Qdrant — so the
document could still surface in retrieval. Current deletes clean up correctly;
this reconciles the historical mess.

Read-only preview by default; pass --apply to actually delete.

    python scripts/cleanup_orphans.py           # show what would be removed
    python scripts/cleanup_orphans.py --apply    # remove it
"""

from __future__ import annotations

import sys

from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.rag.vector_store import get_vector_store


def main(apply: bool) -> None:
    db = SessionLocal()
    try:
        deleted_ids = list(
            db.scalars(select(Document.id).where(Document.deleted_at.isnot(None))).all()
        )
        chunk_count = (
            db.scalar(
                select(func.count())
                .select_from(DocumentChunk)
                .where(DocumentChunk.document_id.in_(deleted_ids))
            )
            if deleted_ids
            else 0
        )

        print(f"soft-deleted documents: {len(deleted_ids)}")
        print(f"orphan chunks under them: {chunk_count}")

        if not apply:
            print("\n(dry run — pass --apply to delete these chunks and their Qdrant points)")
            return
        if not deleted_ids:
            print("nothing to clean.")
            return

        # Postgres: delete chunks (chunk_embeddings cascade via FK).
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id.in_(deleted_ids)))
        db.commit()

        # Qdrant: delete any remaining points per deleted document.
        vector_store = get_vector_store()
        for document_id in deleted_ids:
            vector_store.delete_document(document_id)

        print(f"removed {chunk_count} chunks and Qdrant points for {len(deleted_ids)} documents.")
    finally:
        db.close()


if __name__ == "__main__":
    main(apply="--apply" in sys.argv[1:])
