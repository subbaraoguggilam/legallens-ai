"""Integration tests: upload -> process -> index -> ask -> retrieve -> generate ->
validate citation (design doc section 12), end to end through the HTTP API.
"""
from __future__ import annotations

from tests.conftest import SAMPLE_EMPLOYMENT_TXT, SAMPLE_EMPLOYMENT_TXT_B, signup, upload_sample


def test_full_document_lifecycle(client):
    signup(client)

    doc = upload_sample(client)
    assert doc["status"] == "ready"
    assert doc["page_count"] >= 1
    assert doc["document_type"] == "employment agreement"

    doc_id = doc["id"]

    # Understand My Document
    summary = client.get(f"/api/documents/{doc_id}/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["parties"]
    assert body["dates"]
    assert "not a substitute" in body["disclaimer"].lower()

    # Ask Questions About the Document
    ask = client.post(f"/api/documents/{doc_id}/ask", json={"question": "Can my employer terminate me immediately?"})
    assert ask.status_code == 200
    ask_body = ask.json()
    assert ask_body["confidence"] in {"document_supported", "professional_review_recommended"}
    assert ask_body["citations"], "expected at least one citation for a well-answered question"
    assert any(c["clause"] == "9.1" for c in ask_body["citations"])

    # Follow-up in the same conversation
    convo_id = ask_body["conversation_id"]
    follow_up = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What about the notice period instead?", "conversation_id": convo_id},
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["conversation_id"] == convo_id

    # Clause and Risk Scanner
    risks = client.get(f"/api/documents/{doc_id}/risks")
    assert risks.status_code == 200
    assert "Confidentiality" in risks.json()["categories_found"]

    # Next Steps and Lawyer Question Checklist
    checklist = client.get(f"/api/documents/{doc_id}/checklist")
    assert checklist.status_code == 200
    assert checklist.json()["questions_for_a_lawyer"]

    # Evidence View
    page = client.get(f"/api/documents/{doc_id}/pages/1")
    assert page.status_code == 200
    assert "EMPLOYMENT AGREEMENT" in page.json()["text"]

    # Conversation retrieval
    convo = client.get(f"/api/documents/{doc_id}/conversations/{convo_id}")
    assert convo.status_code == 200
    assert len(convo.json()["messages"]) == 4  # 2 user + 2 assistant

    # Privacy: delete the document and its derived data
    delete = client.delete(f"/api/documents/{doc_id}")
    assert delete.status_code == 204
    assert client.get(f"/api/documents/{doc_id}").status_code == 404


def test_comparison_end_to_end(client):
    signup(client)
    doc_a = upload_sample(client, SAMPLE_EMPLOYMENT_TXT, "a.txt")
    doc_b = upload_sample(client, SAMPLE_EMPLOYMENT_TXT_B, "b.txt")

    resp = client.post(
        "/api/compare", json={"document_id_a": doc_a["id"], "document_id_b": doc_b["id"]}
    )
    assert resp.status_code == 200
    body = resp.json()
    rows_by_category = {r["category"]: r for r in body["rows"]}
    assert rows_by_category["Duration"]["differs"] is True
    assert rows_by_category["Payment"]["differs"] is True
    assert "does not recommend" in body["note"].lower()


def test_question_with_no_evidence_is_marked_insufficient(client):
    signup(client)
    doc = upload_sample(client)
    resp = client.post(
        f"/api/documents/{doc['id']}/ask",
        json={"question": "What is the capital of France?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confidence"] == "insufficient_evidence"
    assert body["citations"] == []


def test_greeting_does_not_hit_retrieval(client):
    signup(client)
    doc = upload_sample(client)
    resp = client.post(f"/api/documents/{doc['id']}/ask", json={"question": "hello"})
    assert resp.status_code == 200
    assert resp.json()["citations"] == []


def test_pdf_page_limit_is_enforced(client, monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("MAX_PAGES", "0")
    get_settings.cache_clear()
    signup(client)
    resp = client.post("/api/documents", files={"file": ("sample.txt", SAMPLE_EMPLOYMENT_TXT.encode(), "text/plain")})
    assert resp.status_code == 413
    get_settings.cache_clear()
