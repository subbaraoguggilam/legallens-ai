# Database Schema

ORM source of truth: `backend/app/models/entities.py`. Works against SQLite
(local development, used by the test suite) and PostgreSQL + pgvector
(docker-compose / production) via the same SQLAlchemy models; embeddings are
stored as a native `vector` column on PostgreSQL and as JSON on SQLite
(`app/models/types.py::EmbeddingType`).

| Table | Key fields |
| --- | --- |
| `users` | `id`, `email` (unique), `password_hash`, `created_at` |
| `documents` | `id`, `user_id`, `filename`, `document_type`, `status`, `error`, `file_ext`, `storage_key`, `size_bytes`, `sha256`, `page_count`, `warnings`, `created_at` |
| `document_pages` | `id`, `document_id`, `page_number`, `text`, `used_ocr` |
| `document_chunks` | `id`, `document_id`, `chunk_index`, `page_number`, `page_end`, `section`, `clause`, `content`, `embedding` |
| `conversations` | `id`, `user_id`, `document_id`, `created_at` |
| `messages` | `id`, `conversation_id`, `role`, `content`, `state`, `created_at` |
| `citations` | `id`, `message_id`, `document_id`, `page_number`, `clause`, `quoted_text` |
| `analyses` | `id`, `document_id`, `analysis_type`, `result` (JSON), `created_at` |
| `comparison_reports` | `id`, `user_id`, `document_a`, `document_b`, `result` (JSON), `created_at` |

All foreign keys cascade on delete, so deleting a `document` removes its pages,
chunks, analyses and conversations (and, transitively, messages and citations);
deleting a `user` removes their documents, conversations and comparison reports.

Tables are created automatically on startup (`app/db.py::init_db`, called from
the FastAPI `lifespan` hook) — there is no separate migration step needed for
this submission. `database/migrations/` is reserved for a future Alembic
migration chain if the schema needs to evolve without a full rebuild.
