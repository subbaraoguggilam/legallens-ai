"""Custom column types."""
from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings

try:  # pgvector is optional; JSON storage is the portable fallback
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover
    Vector = None  # type: ignore[assignment]


class EmbeddingType(TypeDecorator):
    """Stores embeddings as pgvector `vector(N)` on PostgreSQL, JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(get_settings().embedding_dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return [float(x) for x in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return [float(x) for x in value]
