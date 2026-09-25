from app.ai.checklist import build_checklist
from app.ai.risk_scanner import scan
from app.services.clauses import build_chunks
from app.services.extraction import ExtractedPage
from app.services.pipeline import guess_document_type
from tests.conftest import SAMPLE_EMPLOYMENT_TXT


def _chunks_from_text(text: str):
    from app.models import DocumentChunk

    pages = [ExtractedPage(1, text)]
    raw_chunks = build_chunks(pages)
    return [
        DocumentChunk(
            document_id="doc-1",
            chunk_index=c.index,
            page_number=c.page_number,
            page_end=c.page_end,
            section=c.section,
            clause=c.clause,
            content=c.content,
        )
        for c in raw_chunks
    ]


def test_risk_scan_finds_expected_categories():
    chunks = _chunks_from_text(SAMPLE_EMPLOYMENT_TXT)
    findings = scan(chunks)
    categories = {f.category for f in findings}
    assert "Confidentiality" in categories
    assert "Intellectual property" in categories
    assert "Restrictive clauses" in categories
    assert "Dispute resolution and arbitration" in categories


def test_risk_scan_flags_immediate_termination_for_attention():
    chunks = _chunks_from_text(SAMPLE_EMPLOYMENT_TXT)
    findings = scan(chunks)
    flagged = [f for f in findings if f.needs_attention]
    assert flagged, "expected at least one clause flagged for attention"
    assert any("immediately" in f.snippet.lower() for f in flagged)


def test_checklist_uses_language_not_unsupported_claims():
    chunks = _chunks_from_text(SAMPLE_EMPLOYMENT_TXT)
    findings = scan(chunks)
    checklist = build_checklist(findings)
    assert checklist["your_situation"]
    assert checklist["next_steps"]
    assert checklist["questions_for_a_lawyer"]
    # Design-doc requirement: never assert a clause is illegal outright.
    joined = " ".join(checklist["next_steps"]).lower()
    assert "illegal" not in joined


def test_guess_document_type_detects_employment_agreement():
    assert guess_document_type(SAMPLE_EMPLOYMENT_TXT.lower()) == "employment agreement"


def test_guess_document_type_falls_back_to_general():
    assert guess_document_type("some unrelated short note about lunch plans") == "general legal document"
