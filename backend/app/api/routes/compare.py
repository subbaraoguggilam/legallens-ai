"""Contract Comparison (design doc section 2.3)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.comparison import build_comparison
from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db import get_db
from app.models import ComparisonReport, Document, DocumentChunk, User
from app.schemas import CompareRequest

router = APIRouter(prefix="/api/compare", tags=["compare"])


def _owned(db: Session, user: User, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
    if doc.status != "ready":
        raise HTTPException(status_code=409, detail=f"Document {document_id} is not ready yet.")
    return doc


def _chunks(db: Session, document_id: str) -> list[DocumentChunk]:
    return list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
    )


@router.post("")
def compare(payload: CompareRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    if payload.document_id_a == payload.document_id_b:
        raise HTTPException(status_code=422, detail="Choose two different documents to compare.")
    doc_a = _owned(db, user, payload.document_id_a)
    doc_b = _owned(db, user, payload.document_id_b)
    result = build_comparison(doc_a, _chunks(db, doc_a.id), doc_b, _chunks(db, doc_b.id))
    db.add(ComparisonReport(user_id=user.id, document_a=doc_a.id, document_b=doc_b.id, result=result))
    db.commit()
    result["disclaimer"] = get_settings().disclaimer
    return result
