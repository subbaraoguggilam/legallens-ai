"""Clause & risk scanner (design doc section 2.4) — deterministic keyword/pattern
rules over the document's own chunks, so results are auditable and reproducible
without depending on an LLM call.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models import DocumentChunk

CATEGORIES: dict[str, tuple[str, ...]] = {
    "Termination": ("terminat", "dismissal", "end this agreement", "end of employment"),
    "Payment and penalties": ("payment", "penalty", "penalties", "late fee", "interest at", "fine"),
    "Renewal and automatic renewal": ("renew", "automatically renew", "auto-renew", "evergreen"),
    "Liability and indemnity": ("indemnif", "liability", "liable", "hold harmless", "damages"),
    "Confidentiality": ("confidential", "non-disclosure", "nda", "proprietary information"),
    "Intellectual property": ("intellectual property", "copyright", "patent", "trademark", "work product", "assign"),
    "Restrictive clauses": ("non-compete", "non-solicit", "restraint of trade", "shall not compete", "exclusivity"),
    "Dispute resolution and arbitration": ("arbitration", "dispute resolution", "mediation", "arbitrator"),
    "Jurisdiction": ("governing law", "jurisdiction", "venue", "courts of"),
    "Data and privacy": ("personal data", "privacy", "gdpr", "data protection"),
    "Notice period": ("notice period", "written notice", "days notice", "days' notice"),
    "Refund and cancellation": ("refund", "cancellation", "cancel this agreement", "reimburse"),
}

_ATTENTION_MARKERS = (
    "immediately",
    "without notice",
    "sole discretion",
    "irrevocable",
    "perpetual",
    "waive",
    "penalty",
    "forfeit",
    "non-refundable",
    "liquidated damages",
)


@dataclass
class RiskFinding:
    category: str
    page: int
    clause: str | None
    section: str | None
    snippet: str
    needs_attention: bool


def _snippet(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n].rstrip() + "…"


def scan(chunks: list[DocumentChunk]) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    for chunk in chunks:
        low = chunk.content.lower()
        matched = [cat for cat, kws in CATEGORIES.items() if any(k in low for k in kws)]
        if not matched:
            continue
        attention = any(m in low for m in _ATTENTION_MARKERS)
        for cat in matched:
            findings.append(
                RiskFinding(
                    category=cat,
                    page=chunk.page_number,
                    clause=chunk.clause,
                    section=chunk.section,
                    snippet=_snippet(chunk.content),
                    needs_attention=attention,
                )
            )
    return findings


def group_by_category(findings: list[RiskFinding]) -> dict[str, list[RiskFinding]]:
    grouped: dict[str, list[RiskFinding]] = {}
    for f in findings:
        grouped.setdefault(f.category, []).append(f)
    return grouped
