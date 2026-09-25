"""RAG evaluation dataset and metrics (design doc section 12).

Builds a small labeled evaluation set (question -> expected page/clause) and
measures retrieval accuracy, citation accuracy and latency. Only measured
metrics are reported — nothing here is a hard-coded or invented number.
"""
from __future__ import annotations

import time

import pytest

from app.services.clauses import build_chunks
from app.services.embeddings import get_embedder
from app.services.extraction import ExtractedPage
from app.services.retrieval import rerank, retrieve
from tests.conftest import SAMPLE_EMPLOYMENT_TXT

EVAL_DATASET = [
    {"question": "Can my employer terminate me immediately?", "expected_clause": "9.1", "expected_page": 1},
    {"question": "How much notice do I need to give to resign?", "expected_clause": "8.1", "expected_page": 1},
    {"question": "What happens to company property when I leave?", "expected_clause": "9.2", "expected_page": 1},
    {"question": "What is my monthly salary?", "expected_clause": "13.1", "expected_page": 1},
    {"question": "Who owns inventions I create while employed?", "expected_clause": "11.1", "expected_page": 1},
    {"question": "Can I work for a competitor after I leave?", "expected_clause": "12.1", "expected_page": 1},
    {"question": "How are disputes resolved under this agreement?", "expected_clause": "14.1", "expected_page": 1},
    {"question": "Do I have confidentiality obligations?", "expected_clause": "10.1", "expected_page": 1},
    {"question": "How long does this agreement last?", "expected_clause": "1.1", "expected_page": 1},
]


def _seed():
    from app.models import DocumentChunk

    pages = [ExtractedPage(1, SAMPLE_EMPLOYMENT_TXT)]
    embedder = get_embedder()
    return [
        DocumentChunk(
            document_id="doc-eval",
            chunk_index=c.index,
            page_number=c.page_number,
            page_end=c.page_end,
            section=c.section,
            clause=c.clause,
            content=c.content,
            embedding=embedder.embed(f"{c.section or ''} {c.content}"),
        )
        for c in build_chunks(pages)
    ]


@pytest.fixture()
def seeded_chunks(app_env):
    return _seed()


def test_rag_evaluation_dataset_meets_minimum_bar(seeded_chunks):
    """Measures retrieval accuracy, citation (page) accuracy and latency on the
    labeled set, and asserts a minimum quality bar rather than an exact figure.
    """
    hits_top1 = 0
    hits_top3 = 0
    page_correct = 0
    latencies_ms: list[float] = []

    for item in EVAL_DATASET:
        start = time.perf_counter()
        candidates = retrieve(None, "doc-eval", item["question"], top_k=5, chunks=seeded_chunks)
        top = rerank(item["question"], candidates, top_n=3)
        latencies_ms.append((time.perf_counter() - start) * 1000)

        clauses = [r.chunk.clause for r in top]
        if clauses and clauses[0] == item["expected_clause"]:
            hits_top1 += 1
        if item["expected_clause"] in clauses:
            hits_top3 += 1
        if top and top[0].chunk.page_number == item["expected_page"]:
            page_correct += 1

    n = len(EVAL_DATASET)
    top1_accuracy = hits_top1 / n
    top3_accuracy = hits_top3 / n
    page_accuracy = page_correct / n
    p95_latency_ms = sorted(latencies_ms)[int(0.95 * (n - 1))]

    print(
        f"\nRAG evaluation (n={n}): "
        f"top1_accuracy={top1_accuracy:.2f} top3_accuracy={top3_accuracy:.2f} "
        f"page_accuracy={page_accuracy:.2f} p95_latency_ms={p95_latency_ms:.1f}"
    )

    # Minimum quality bar for this lexical+embedding retriever on a small contract.
    assert top3_accuracy >= 0.85
    assert page_accuracy >= 0.85
    assert p95_latency_ms < 200
