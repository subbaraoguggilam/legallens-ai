"""Contract comparison (design doc section 2.3): side-by-side category table.

Deterministic pattern extraction per category, keeping page/clause provenance,
so the comparison never depends on an LLM call and cannot silently hallucinate a
number. The system presents differences and sources without recommending a choice.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import Document, DocumentChunk

DURATION_RE = re.compile(r"\b(\d{1,3})\s*(day|month|year)s?\b", re.IGNORECASE)
NOTICE_RE = re.compile(r"\b(\d{1,3})\s*(day|month)s?\s*(?:’|')?\s*(?:written\s+)?notice", re.IGNORECASE)
MONEY_RE = re.compile(r"(?:₹|Rs\.?|INR|\$|USD|£|GBP|€|EUR)\s?[\d,]+(?:\.\d+)?", re.IGNORECASE)

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Duration": ("term of this agreement", "duration", "this agreement shall continue"),
    "Notice period": ("notice period", "written notice", "days notice", "days' notice"),
    "Termination": ("terminat",),
    "Payment": ("payment", "salary", "compensation", "fee", "rent"),
    "Confidentiality": ("confidential", "non-disclosure"),
    "IP ownership": ("intellectual property", "copyright", "work product", "assign"),
    "Dispute resolution": ("arbitration", "court", "jurisdiction", "mediation"),
}


@dataclass
class CategoryResult:
    category: str
    value: str
    page: int | None
    clause: str | None


def _find_chunk(chunks: list[DocumentChunk], keywords: tuple[str, ...]) -> DocumentChunk | None:
    for c in chunks:
        low = c.content.lower()
        if any(k in low for k in keywords):
            return c
    return None


def _value_for(category: str, chunk: DocumentChunk | None) -> str:
    if chunk is None:
        return "Not found in document"
    text = chunk.content
    if category == "Duration":
        m = DURATION_RE.search(text)
        return f"{m.group(1)} {m.group(2)}(s)" if m else "Mentioned, see source"
    if category == "Notice period":
        m = NOTICE_RE.search(text)
        return f"{m.group(1)} {m.group(2)}(s)" if m else "Mentioned, see source"
    if category == "Termination":
        return f"Clause {chunk.clause}" if chunk.clause else "See source"
    if category == "Payment":
        m = MONEY_RE.search(text)
        return m.group(0) if m else "Mentioned, see source"
    if category in ("Confidentiality",):
        return "Yes"
    if category == "IP ownership":
        low = text.lower()
        if "joint" in low:
            return "Joint"
        if "employer" in low or "company" in low:
            return "Employer / company"
        if "employee" in low or "contractor" in low:
            return "Employee / contractor"
        return "See source"
    if category == "Dispute resolution":
        low = text.lower()
        if "arbitrat" in low:
            return "Arbitration"
        if "mediat" in low:
            return "Mediation"
        if "court" in low:
            return "Court"
        return "See source"
    return "See source"


def compare_categories(chunks: list[DocumentChunk]) -> list[CategoryResult]:
    results = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        chunk = _find_chunk(chunks, keywords)
        results.append(
            CategoryResult(
                category=category,
                value=_value_for(category, chunk),
                page=chunk.page_number if chunk else None,
                clause=chunk.clause if chunk else None,
            )
        )
    return results


def build_comparison(doc_a: Document, chunks_a: list[DocumentChunk], doc_b: Document, chunks_b: list[DocumentChunk]) -> dict:
    rows_a = {r.category: r for r in compare_categories(chunks_a)}
    rows_b = {r.category: r for r in compare_categories(chunks_b)}
    rows = []
    for category in CATEGORY_KEYWORDS:
        a, b = rows_a[category], rows_b[category]
        rows.append(
            {
                "category": category,
                "a": {"value": a.value, "page": a.page, "clause": a.clause},
                "b": {"value": b.value, "page": b.page, "clause": b.clause},
                "differs": a.value != b.value,
            }
        )
    return {
        "document_a": {"id": doc_a.id, "filename": doc_a.filename},
        "document_b": {"id": doc_b.id, "filename": doc_b.filename},
        "rows": rows,
        "note": (
            "This table presents differences and their sources. It does not recommend which "
            "document or terms to choose."
        ),
    }
