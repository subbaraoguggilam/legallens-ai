"""Understand My Document + Clause/Risk Scanner + Checklist (sections 2.1, 2.4, 2.5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.checklist import build_checklist
from app.ai.risk_scanner import scan
from app.ai.summary import extract_facts, summarize
from app.api.deps import get_owned_document
from app.core.config import get_settings
from app.db import get_db
from app.models import Analysis, Document, DocumentChunk
from app.schemas import ChecklistResponse, RiskFindingOut, RiskScanResponse, SummaryResponse

router = APIRouter(prefix="/api/documents/{document_id}", tags=["analyze"])


def _chunks(db: Session, document_id: str) -> list[DocumentChunk]:
    return list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
    )


def _cache_get(db: Session, document_id: str, kind: str) -> dict | None:
    row = db.scalar(
        select(Analysis)
        .where(Analysis.document_id == document_id, Analysis.analysis_type == kind)
        .order_by(Analysis.created_at.desc())
    )
    return row.result if row else None


def _cache_set(db: Session, document_id: str, kind: str, result: dict) -> None:
    db.add(Analysis(document_id=document_id, analysis_type=kind, result=result))
    db.commit()


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(doc: Document = Depends(get_owned_document), db: Session = Depends(get_db)) -> SummaryResponse:
    cached = _cache_get(db, doc.id, "summary")
    if cached is None:
        chunks = _chunks(db, doc.id)
        full_text = "\n".join(c.content for c in chunks)
        facts = extract_facts(full_text)
        summary_text = await summarize(chunks, facts)
        cached = {
            "summary": summary_text,
            "parties": facts.parties,
            "dates": facts.dates,
            "obligations": facts.obligation_snippets,
        }
        _cache_set(db, doc.id, "summary", cached)
    return SummaryResponse(document_id=doc.id, document_type=doc.document_type, disclaimer=get_settings().disclaimer, **cached)


@router.get("/risks", response_model=RiskScanResponse)
def get_risks(doc: Document = Depends(get_owned_document), db: Session = Depends(get_db)) -> RiskScanResponse:
    findings = scan(_chunks(db, doc.id))
    return RiskScanResponse(
        document_id=doc.id,
        findings=[RiskFindingOut(**f.__dict__) for f in findings],
        categories_found=sorted({f.category for f in findings}),
        review_note=(
            "Flagged clauses may warrant professional review. This is not a determination that "
            "any clause is unusual, unfair or unenforceable."
        ),
        disclaimer=get_settings().disclaimer,
    )


@router.get("/checklist", response_model=ChecklistResponse)
def get_checklist(doc: Document = Depends(get_owned_document), db: Session = Depends(get_db)) -> ChecklistResponse:
    findings = scan(_chunks(db, doc.id))
    data = build_checklist(findings)
    return ChecklistResponse(document_id=doc.id, disclaimer=get_settings().disclaimer, **data)
