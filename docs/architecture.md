# Architecture

## Overview

LegalLens AI is an evidence-grounded legal document assistant. A person uploads a
document; the system extracts text with page mapping, segments it into numbered
clauses, indexes those clauses for retrieval, and answers questions, generates
summaries, scans for notable clauses, compares documents, and builds a checklist —
always tying every claim back to a specific page and clause in the original file.

```
User
  |  PDF / DOCX / TXT, question, or comparison request
  v
Frontend (Next.js + TypeScript)
  |  HTTPS, cookie session
  v
Backend API (FastAPI)
  |
  |-- Auth (JWT session cookie, bcrypt password hashing)
  |-- Document Service
  |     |-- Upload validation (extension, MIME, signature, size, page count)
  |     |-- Malware scan (heuristics + optional ClamAV)
  |     |-- Extraction (PyMuPDF + OCR, python-docx, plain text) -> pages
  |     |-- Clause segmentation & chunking -> page/clause-tagged chunks
  |     |-- Embedding (hashing embedder; swappable for a neural model)
  |     `-- Encrypted storage (Fernet) of the original file
  |
  |-- AI Service
  |     |-- Retrieval: BM25 + cosine similarity, metadata-scoped to one document
  |     |-- Rerank: lexical coverage of the question's topic words
  |     |-- Guardrails: prompt-injection sanitisation, PII redaction, strict
  |     |     system/application/evidence/question instruction hierarchy
  |     |-- LLM provider abstraction: mock | gemini | groq (same interface)
  |     `-- Evidence validator: downgrades or rejects ungrounded claims
  |
  `-- PostgreSQL + pgvector (SQLite for local development)
```

## Core workflow (as in the project design doc)

1. **Document processing** — text extraction, OCR for scanned pages, page and
   clause mapping (`app/services/extraction.py`, `app/services/clauses.py`).
2. **Legal knowledge layer** — chunking, metadata (page/clause/section), embeddings
   (`app/services/embeddings.py`, `app/services/pipeline.py`).
3. **AI legal reasoning** — RAG retrieval + reranking, rule-based clause/risk
   scanning, safety guardrails (`app/ai/`).
4. **Evidence validator** — citation/grounding verification before any answer
   reaches the user (`app/ai/citation_validator.py`).
5. **User output** — summary, risks, comparison, checklist, questions/next steps
   (`app/api/routes/analyze.py`, `compare.py`, `ask.py`).

## Why a hashing embedder by default

The default embedder (`HashingEmbedder`) is a deterministic feature-hashing
embedder over uni/bi-grams. It needs no model download and no network access, so
the whole system — including the RAG evaluation tests — runs offline and
reproducibly. Swap in a neural embedding model by implementing the `Embedder`
protocol in `app/services/embeddings.py`; nothing else changes, because the
column that stores embeddings (`pgvector` on PostgreSQL, JSON elsewhere) and the
retrieval code are agnostic to how a vector was produced.

## Why an LLM provider abstraction

`app/ai/providers.py` defines `LLMProvider` with a single `generate(system, prompt)`
method. `GeminiProvider` and `GroqProvider` implement it against their respective
HTTP APIs; `MockProvider` implements it deterministically offline (used by default
and in tests, so the whole product works and is testable without an API key).
Switching providers is one environment variable: `LLM_PROVIDER=gemini|groq|mock`.

## Database design

See `database/schema.md` for the full table list. In short: `users` own
`documents`; each document has `document_pages` (raw extracted text per page) and
`document_chunks` (clause-tagged, embedded pieces used for retrieval);
`conversations` hold `messages`, and assistant messages carry `citations` back to
a specific page/clause; `analyses` cache summary/risk results;
`comparison_reports` record a comparison between two documents.

## Repository layout

```
legallens/
├── frontend/            Next.js + TypeScript UI
├── backend/              FastAPI + Python API
│   ├── app/
│   │   ├── api/routes/   HTTP endpoints
│   │   ├── ai/           RAG, providers, guardrails, risk scanner, checklist
│   │   ├── core/         config, security, logging, rate limiting, crypto
│   │   ├── models/       SQLAlchemy ORM
│   │   ├── schemas.py    Pydantic request/response models
│   │   └── services/     extraction, chunking, embeddings, retrieval, storage
│   └── tests/            unit, integration, security, rag, evaluation
├── database/             seed script, schema notes
├── docs/                 this file, security.md, api.md, threat-model.md
├── docker-compose.yml
└── .env.example
```
