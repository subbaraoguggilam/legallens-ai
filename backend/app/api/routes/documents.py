"""Document upload, listing, retrieval, deletion (design doc sections 2.1, 7, 8)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_document
from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.db import get_db
from app.models import Conversation, Document, User
from app.schemas import DocumentOut
from app.services.pipeline import process_upload
from app.services.storage import delete_file
from app.services.upload_validation import UploadRejected

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=201, dependencies=[Depends(rate_limiter("upload"))])
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Document:
    settings = get_settings()
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb} MB limit.")
    try:
        return process_upload(db, user.id, file.filename, file.content_type, data)
    except UploadRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Document]:
    return list(
        db.scalars(
            select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
        )
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(doc: Document = Depends(get_owned_document)) -> Document:
    return doc


@router.delete("/{document_id}", status_code=204)
def delete_document(doc: Document = Depends(get_owned_document), db: Session = Depends(get_db)) -> None:
    """Privacy: lets the user delete their document and its derived data entirely."""
    if doc.storage_key:
        delete_file(doc.storage_key)
    db.delete(doc)  # cascades to pages, chunks, analyses, conversations, messages, citations
    db.commit()


@router.delete("/{document_id}/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    doc: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
) -> None:
    convo = db.get(Conversation, conversation_id)
    if not convo or convo.document_id != doc.id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(convo)
    db.commit()
