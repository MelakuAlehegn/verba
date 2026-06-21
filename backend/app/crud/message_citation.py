from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.message_citation import MessageCitation


def create_message_citation(
    db: Session,
    *,
    message_id: UUID,
    document_id: UUID | None,
    chunk_id: UUID | None,
    rank: int,
    score: float | None = None,
    quote_preview: str | None = None,
) -> MessageCitation:
    citation = MessageCitation(
        message_id=message_id,
        document_id=document_id,
        chunk_id=chunk_id,
        rank=rank,
        score=score,
        quote_preview=quote_preview,
    )
    db.add(citation)
    db.flush()
    return citation
