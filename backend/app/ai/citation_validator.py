"""Evidence Validator (design doc section 6): checks the model's citations are real
and grounded before anything reaches the user.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass

from app.services.retrieval import Retrieved

VALID_STATES = {
    "document_supported",
    "general_information",
    "insufficient_evidence",
    "professional_review_recommended",
}


@dataclass
class ValidatedAnswer:
    answer: str
    confidence: str
    citations: list[dict]


def _snippet(text: str, length: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= length else text[:length].rstrip() + "…"


def _is_grounded(answer: str, evidence_texts: list[str]) -> bool:
    """Cheap groundedness check: does the answer overlap enough with cited evidence?

    Not a substitute for a real NLI/entailment model, but catches unrelated or
    fabricated answers before they reach the user.
    """
    if not evidence_texts:
        return False
    joined = " ".join(evidence_texts).lower()
    ratio = difflib.SequenceMatcher(None, answer.lower()[:400], joined[:4000]).find_longest_match(
        0, min(400, len(answer)), 0, min(4000, len(joined))
    ).size
    return ratio >= 8 or any(w in joined for w in answer.lower().split() if len(w) > 6)


def validate(raw: dict, retrieved: list[Retrieved]) -> ValidatedAnswer:
    """Downgrade or reject anything the model claims that isn't actually backed by evidence."""
    answer = str(raw.get("answer") or "").strip()
    confidence = raw.get("confidence") if raw.get("confidence") in VALID_STATES else None
    idxs = raw.get("citation_indices")
    idxs = [i for i in idxs if isinstance(i, int) and 0 <= i < len(retrieved)] if isinstance(idxs, list) else []

    if not answer:
        return ValidatedAnswer(
            "The system could not generate a grounded answer for this question.",
            "insufficient_evidence",
            [],
        )

    if not retrieved:
        return ValidatedAnswer(answer, "insufficient_evidence", [])

    cited = [retrieved[i] for i in idxs] or retrieved[:1]
    grounded = _is_grounded(answer, [r.chunk.content for r in cited])

    if confidence is None:
        confidence = "document_supported" if grounded else "insufficient_evidence"
    elif confidence == "document_supported" and not grounded:
        # Model claimed grounding we can't verify: downgrade rather than trust it.
        confidence = "professional_review_recommended"

    citations = []
    if confidence in ("document_supported", "professional_review_recommended"):
        for r in cited:
            citations.append(
                {
                    "document_id": r.chunk.document_id,
                    "page": r.chunk.page_number,
                    "clause": r.chunk.clause,
                    "quoted_text": _snippet(r.chunk.content),
                }
            )

    return ValidatedAnswer(answer, confidence, citations)
