"""Embeddings.

The default embedder is a deterministic *feature-hashing* embedder (signed hashed
uni/bi-grams with sublinear TF and L2 normalisation). It needs no model download or
network access, so the whole system runs offline and tests are reproducible.

`Embedder` is an interface: swap in a neural embedding model (e.g. a sentence-transformer
or a hosted embedding API) by implementing `embed` and returning vectors of
`settings.embedding_dim` — the pgvector column and retrieval code do not change.
"""
from __future__ import annotations

import hashlib
import math
from collections import Counter
from typing import Protocol

from app.core.config import get_settings
from app.services.text_utils import tokenize


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


def _hash(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big")


class HashingEmbedder:
    def __init__(self, dim: int | None = None):
        self.dim = dim or get_settings().embedding_dim

    def embed(self, text: str) -> list[float]:
        toks = tokenize(text)
        feats = Counter(toks)
        feats.update(f"{a}_{b}" for a, b in zip(toks, toks[1:], strict=False))
        vec = [0.0] * self.dim
        for feat, tf in feats.items():
            h = _hash(feat)
            sign = 1.0 if (h >> 63) & 1 else -1.0
            vec[h % self.dim] += sign * (1.0 + math.log(tf))
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = HashingEmbedder()
    return _embedder


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))
