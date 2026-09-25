"""Hybrid retrieval: embedding cosine similarity + BM25, with metadata filtering.

Flow (mirrors the design doc):  all chunks of ONE document (metadata filter)
→ similarity search → top-k → optional rerank → top-n for the LLM.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import DocumentChunk
from app.services.embeddings import cosine, get_embedder
from app.services.text_utils import STOPWORDS, SYNONYMS, expand_query, stem, tokenize

# Words that describe *asking* rather than the topic being asked about.
QUESTION_FILLER = frozenset(
    """agreement contract document clause clauses say says said state states explain tell mention
    mentions include includes provide provides allow allows permit permitted get make happen happens
    many much like need want know mean means describe describes cover covers give gives find show
    please help understand about specific exactly really""".split()
)


def core_terms(query: str) -> list[str]:
    import re

    words = re.findall(r"[a-z][a-z'\-]+", query.lower())
    return [w for w in words if w not in STOPWORDS and w not in QUESTION_FILLER and len(w) > 2]


def term_coverage(query: str, text: str) -> float:
    """Fraction of the question's topic words (or their legal synonyms) found in `text`."""
    terms = core_terms(query)
    if not terms:
        return 0.0
    toks = set(tokenize(text))
    hit = 0
    for w in terms:
        if stem(w) in toks or any(stem(x) in toks for x in SYNONYMS.get(w, ())):
            hit += 1
    return hit / len(terms)


@dataclass
class Retrieved:
    chunk: DocumentChunk
    score: float
    vector_score: float
    keyword_score: float
    coverage: float = 0.0


def _bm25(query_terms: list[str], docs: list[list[str]], k1: float = 1.4, b: float = 0.75) -> list[float]:
    n = len(docs)
    if not n or not query_terms:
        return [0.0] * n
    avgdl = sum(len(d) for d in docs) / n or 1.0
    df: Counter[str] = Counter()
    for d in docs:
        df.update(set(d))
    scores = []
    for d in docs:
        tf = Counter(d)
        s = 0.0
        for t in set(query_terms):
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avgdl))
        scores.append(s)
    return scores


def _norm(values: list[float]) -> list[float]:
    m = max(values, default=0.0)
    return [v / m if m > 0 else 0.0 for v in values]


def retrieve(
    db: Session,
    document_id: str,
    query: str,
    *,
    top_k: int | None = None,
    chunks: list[DocumentChunk] | None = None,
) -> list[Retrieved]:
    s = get_settings()
    top_k = top_k or s.retrieve_top_k
    if chunks is None:
        chunks = list(
            db.scalars(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
            )
        )
    if not chunks:
        return []

    expanded = expand_query(query)
    q_vec = get_embedder().embed(expanded)
    q_terms = tokenize(expanded)
    # Section titles are part of what a clause "is about", so include them for matching.
    docs_tokens = [tokenize(f"{c.section or ''} {c.content}") for c in chunks]
    kw = _norm(_bm25(q_terms, docs_tokens))
    vec = [max(0.0, cosine(q_vec, c.embedding or [])) for c in chunks]
    vec_n = _norm(vec)

    results = [
        Retrieved(
            c,
            0.55 * vn + 0.45 * kn,
            v,
            k,
            term_coverage(query, f"{c.section or ''} {c.content}"),
        )
        for c, vn, kn, v, k in zip(chunks, vec_n, kw, vec, kw, strict=True)
    ]
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]


def rerank(query: str, results: list[Retrieved], top_n: int | None = None) -> list[Retrieved]:
    """Lightweight lexical-overlap reranker (query-term coverage + clause boost).

    Replace with a cross-encoder for higher accuracy; the interface stays the same.
    """
    top_n = top_n or get_settings().rerank_top_k
    rescored = []
    for r in results:
        bonus = 0.05 if r.chunk.clause else 0.0
        rescored.append(
            Retrieved(
                r.chunk,
                0.6 * r.score + 0.4 * r.coverage + bonus,
                r.vector_score,
                r.keyword_score,
                r.coverage,
            )
        )
    rescored.sort(key=lambda r: r.score, reverse=True)
    return rescored[:top_n]
