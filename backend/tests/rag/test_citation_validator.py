from app.ai.citation_validator import validate
from app.models import DocumentChunk
from app.services.retrieval import Retrieved


def _retrieved(content: str, clause: str = "9.1", page: int = 1) -> Retrieved:
    chunk = DocumentChunk(
        document_id="doc-1",
        chunk_index=0,
        page_number=page,
        page_end=page,
        section="9. Termination",
        clause=clause,
        content=content,
    )
    return Retrieved(chunk=chunk, score=0.9, vector_score=0.9, keyword_score=0.9, coverage=0.8)


def test_grounded_answer_is_accepted_with_citations():
    retrieved = [_retrieved("The Employer may terminate this agreement immediately for cause.")]
    raw = {
        "answer": "The employer may terminate immediately for cause, per clause 9.1.",
        "confidence": "document_supported",
        "citation_indices": [0],
    }
    result = validate(raw, retrieved)
    assert result.confidence == "document_supported"
    assert result.citations
    assert result.citations[0]["clause"] == "9.1"


def test_unsupported_claim_is_downgraded_not_trusted():
    retrieved = [_retrieved("The Employer shall pay the Employee a monthly salary of Rs. 55,000.")]
    raw = {
        "answer": "You are entitled to unlimited paid vacation for life.",
        "confidence": "document_supported",
        "citation_indices": [0],
    }
    result = validate(raw, retrieved)
    # The model claimed grounding but the answer isn't supported by the evidence text.
    assert result.confidence != "document_supported"


def test_empty_evidence_yields_insufficient_evidence():
    raw = {"answer": "Some answer.", "confidence": "document_supported", "citation_indices": []}
    result = validate(raw, [])
    assert result.confidence == "insufficient_evidence"
    assert result.citations == []


def test_invalid_citation_indices_are_dropped():
    retrieved = [_retrieved("Some clause text about termination.")]
    raw = {
        "answer": "This explains the termination clause.",
        "confidence": "document_supported",
        "citation_indices": [5, -1, "x"],
    }
    result = validate(raw, retrieved)
    # Falls back to the top retrieved chunk rather than crashing on bad indices.
    assert result.citations
    assert result.citations[0]["clause"] == "9.1"


def test_empty_answer_is_rejected():
    result = validate({"answer": "", "confidence": "document_supported"}, [_retrieved("text")])
    assert result.confidence == "insufficient_evidence"
    assert "could not generate" in result.answer.lower()


def test_invalid_confidence_value_is_normalized():
    retrieved = [_retrieved("The Employer may terminate this agreement immediately for cause.")]
    raw = {
        "answer": "The employer may terminate immediately for cause.",
        "confidence": "definitely_yes_100_percent",
        "citation_indices": [0],
    }
    result = validate(raw, retrieved)
    assert result.confidence in {
        "document_supported",
        "general_information",
        "insufficient_evidence",
        "professional_review_recommended",
    }
