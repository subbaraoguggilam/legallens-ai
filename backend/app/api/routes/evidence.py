"""Evidence View (design doc section 14): the original page text behind an AI claim."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_owned_document
from app.db import get_db
from app.models import Document, DocumentPage
from app.schemas import EvidencePageOut

router = APIRouter(prefix="/api/documents/{document_id}", tags=["evidence"])


@router.get("/pages/{page_number}", response_model=EvidencePageOut)
def get_page(
    page_number: int,
    doc: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
) -> EvidencePageOut:
    page = db.scalar(
        select(DocumentPage).where(
            DocumentPage.document_id == doc.id, DocumentPage.page_number == page_number
        )
    )
    if not page:
        raise HTTPException(status_code=404, detail="Page not found.")
    return EvidencePageOut(document_id=doc.id, page=page.page_number, page_count=doc.page_count, text=page.text)
