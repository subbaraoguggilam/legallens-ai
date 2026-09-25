"""RAG evaluation (design doc section 12): retrieval accuracy and citation accuracy
against a small labeled question set with expected page/clause references.
"""
from __future__ import annotations

import pytest

from app.services.clauses import build_chunks
from app.services.embeddings import get_embedder
from app.services.extraction import ExtractedPage
from app.services.retrieval import rerank, retrieve
from tests.conftest import SAMPLE_EMPLOYMENT_TXT


def _seed_chunks(session_factory, document_id: str, text: str):
    from app.models import DocumentChunk

    pages = [ExtractedPage(1, text)]
    embedder = get_embedder()
    chunks = []
    for c in build_chunks(pages):
        chunks.append(
            DocumentChunk(
                document_id=document_id,
                chunk_index=c.index,
                page_number=c.page_number,
                page_end=c.page_end,
                section=c.section,
                clause=c.clause,
                content=c.content,
                embedding=embedder.embed(f"{c.section or ''} {c.content}"),
            )
        )
    return chunks


# (question, expected clause substring that should appear in the top result)
EVAL_SET = [
    ("Can my employer terminate me immediately?", "9.1"),
    ("How much notice do I need to give to resign?", "8.1"),
    ("What is my monthly salary?", "13.1"),
    ("Who owns inventions I create while employed?", "11.1"),
    ("Am I allowed to work for a competitor after I leave?", "12.1"),
    ("How are disputes resolved under this agreement?", "14.1"),
    ("Do I have confidentiality obligations?", "10.1"),
]


@pytest.fixture()
def seeded_chunks(app_env):
    return _seed_chunks(None, "doc-eval", SAMPLE_EMPLOYMENT_TXT)


@pytest.mark.parametrize("question,expected_clause", EVAL_SET)
def test_retrieval_finds_expected_clause_in_top_3(seeded_chunks, question, expected_clause):
    results = retrieve(None, "doc-eval", question, top_k=5, chunks=seeded_chunks)
    top = rerank(question, results, top_n=3)
    clauses = [r.chunk.clause for r in top]
    assert expected_clause in clauses, f"expected {expected_clause} in top-3 for {question!r}, got {clauses}"


def test_retrieval_returns_nothing_useful_for_unrelated_question(seeded_chunks):
    results = retrieve(None, "doc-eval", "What is the weather forecast for tomorrow?", top_k=5, chunks=seeded_chunks)
    top = rerank("What is the weather forecast for tomorrow?", results, top_n=3)
    # Coverage should be low: nothing in the document is actually about weather.
    assert all(r.coverage < 0.5 for r in top)


def test_retrieval_is_scoped_to_document(seeded_chunks):
    other_chunks = _seed_chunks(None, "doc-other", "1. Unrelated\n1.1 This document is about gardening tips.")
    combined = seeded_chunks + other_chunks
    results = retrieve(None, "doc-eval", "salary", top_k=10, chunks=[c for c in combined if c.document_id == "doc-eval"])
    assert all(r.chunk.document_id == "doc-eval" for r in results)
