"""End-to-end document processing pipeline: upload -> extract -> chunk -> embed -> store."""
from __future__ import annotations

import hashlib

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Document, DocumentChunk, DocumentPage
from app.services.clauses import build_chunks
from app.services.embeddings import get_embedder
from app.services.extraction import extract
from app.services.malware_scan import scan_bytes
from app.services.storage import save_encrypted
from app.services.upload_validation import UploadRejected, validate_upload

log = get_logger("pipeline")

DOC_TYPE_HINTS: dict[str, tuple[str, ...]] = {
    "employment agreement": ("employment", "employer", "employee", "job title", "salary"),
    "rental agreement": ("lessee", "lessor", "landlord", "tenant", "rent", "premises"),
    "nda": ("non-disclosure", "confidential information", "nda", "disclosing party"),
    "service agreement": ("services", "scope of work", "service provider", "client"),
    "loan agreement": ("loan", "principal", "interest rate", "borrower", "lender", "repayment"),
    "insurance document": ("policyholder", "premium", "coverage", "insured", "claim"),
    "terms and conditions": ("terms and conditions", "terms of service", "acceptable use"),
}


def guess_document_type(text: str) -> str:
    low = text.lower()
    best, best_hits = "general legal document", 0
    for label, kws in DOC_TYPE_HINTS.items():
        hits = sum(1 for k in kws if k in low)
        if hits > best_hits:
            best, best_hits = label, hits
    return best


def process_upload(
    db: Session, user_id: str, filename: str | None, content_type: str | None, data: bytes
) -> Document:
    validated = validate_upload(filename, content_type, data)

    scan = scan_bytes(validated.data, validated.ext)
    if not scan.clean:
        raise UploadRejected(scan.reason or "Upload rejected by malware scan.", 422)

    doc = Document(
        user_id=user_id,
        filename=validated.filename,
        file_ext=validated.ext,
        size_bytes=len(validated.data),
        sha256=hashlib.sha256(validated.data).hexdigest(),
        status="processing",
    )
    db.add(doc)
    db.flush()

    try:
        result = extract(validated.data, validated.ext)
        doc.storage_key = save_encrypted(user_id, validated.data)
        doc.page_count = len(result.pages)
        doc.warnings = result.warnings
        doc.document_type = guess_document_type(result.full_text)

        for p in result.pages:
            db.add(DocumentPage(document_id=doc.id, page_number=p.number, text=p.text, used_ocr=p.used_ocr))

        chunks = build_chunks(result.pages)
        embedder = get_embedder()
        for c in chunks:
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c.index,
                    page_number=c.page_number,
                    page_end=c.page_end,
                    section=c.section,
                    clause=c.clause,
                    content=c.content,
                    embedding=embedder.embed(f"{c.section or ''} {c.content}"),
                )
            )
        doc.status = "ready"
    except UploadRejected:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        log.error("processing_failed", extra={"ctx": {"document_id": doc.id, "error": str(exc)}})
        doc.status = "failed"
        doc.error = "Document processing failed. Please try re-uploading the file."

    db.commit()
    db.refresh(doc)
    return doc
