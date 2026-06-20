from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.document_service import (
    delete_document_for_user,
    get_document_for_user,
    list_documents_for_user,
    upload_document_for_user,
)
from app.storage import StorageClient, get_storage_client

router = APIRouter(prefix="/documents", tags=["documents"])


def get_owned_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    document = get_document_for_user(db, current_user, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("", response_model=list[DocumentRead])
def list_documents_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentRead]:
    documents = list_documents_for_user(db, current_user)
    return [DocumentRead.model_validate(document) for document in documents]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: StorageClient = Depends(get_storage_client),
) -> DocumentRead:
    # Sync handler → FastAPI runs it in a threadpool, so the blocking storage
    # + DB calls don't stall the event loop. (Heavy ingestion still moves to a
    # worker later; this request just stores bytes + a row.)
    settings = get_settings()
    allowed_extensions = settings.upload_allowed_extension_set

    filename = os.path.basename(file.filename or "upload")
    extension = os.path.splitext(filename)[1].lower()
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{extension}'. Allowed: {sorted(allowed_extensions)}",
        )

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > settings.upload_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large"
        )

    content_type = file.content_type or "application/octet-stream"
    document = upload_document_for_user(
        db, current_user, storage, filename=filename, content_type=content_type, data=data
    )
    return DocumentRead.model_validate(document)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document_endpoint(document: Document = Depends(get_owned_document)) -> DocumentRead:
    return DocumentRead.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_endpoint(
    document: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
) -> None:
    delete_document_for_user(db, document, storage)
