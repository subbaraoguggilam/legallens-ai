# API Reference

Base URL: `http://localhost:8000` (see `.env.example` / `NEXT_PUBLIC_API_BASE`).
Interactive OpenAPI docs are also available at `/docs` and `/redoc` when the
backend is running.

All endpoints except `/api/health`, `/api/auth/signup` and `/api/auth/login`
require a valid session cookie (set automatically by signup/login). All
document-scoped endpoints return `404` if the document does not exist or is not
owned by the current user.

## Auth

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/auth/signup` | `{email, password}` → creates an account and sets the session cookie. |
| POST | `/api/auth/login` | `{email, password}` → sets the session cookie. |
| POST | `/api/auth/logout` | Clears the session cookie. |
| GET | `/api/auth/me` | Returns the current user. |

## Documents

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/documents` | Multipart upload (`file`). Validates, scans, extracts, chunks, embeds and stores the document; returns it once processed. |
| GET | `/api/documents` | Lists the current user's documents, newest first. |
| GET | `/api/documents/{id}` | Fetches one document. |
| DELETE | `/api/documents/{id}` | Deletes a document and all derived data (pages, chunks, analyses, conversations). |
| GET | `/api/documents/{id}/pages/{n}` | Returns the raw extracted text of page `n` (Evidence View). |

## Understanding a document

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/documents/{id}/summary` | Plain-language summary, parties, dates, notable obligations. Cached after first call. |
| GET | `/api/documents/{id}/risks` | Clause/risk scan across 12 categories (termination, payment, IP, arbitration, etc.), each with a page/clause reference. |
| GET | `/api/documents/{id}/checklist` | "Your situation" summary, next steps, and questions to ask a lawyer, personalised to the detected clauses. |

## Ask

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/documents/{id}/ask` | `{question, conversation_id?}` → retrieves relevant clauses, generates a grounded answer, validates its citations, and returns `{answer, confidence, citations[], disclaimer}`. Starts a new conversation if `conversation_id` is omitted. |
| GET | `/api/documents/{id}/conversations/{conversation_id}` | Returns the full message history with citations. |
| DELETE | `/api/documents/{id}/conversations/{conversation_id}` | Deletes a conversation. |

`confidence` is one of `document_supported`, `general_information`,
`insufficient_evidence`, `professional_review_recommended` — see
`docs/architecture.md` and `app/ai/citation_validator.py`.

## Compare

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/compare` | `{document_id_a, document_id_b}` → a category-by-category comparison table (duration, notice period, termination, payment, confidentiality, IP ownership, dispute resolution), each cell with its page/clause source. Presents differences without recommending a choice. |

## Health

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Liveness check; also reports the configured LLM provider. |

## Example: ask a question

```bash
curl -s -c cookies.txt -X POST http://localhost:8000/api/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"Passw0rd123"}'

curl -s -b cookies.txt -F "file=@employment.pdf" http://localhost:8000/api/documents
# => {"id": "...", "status": "ready", ...}

curl -s -b cookies.txt -X POST http://localhost:8000/api/documents/<id>/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "Can my employer terminate me immediately?"}'
# => {"answer": "...", "confidence": "document_supported",
#     "citations": [{"page": 1, "clause": "9.1", "quoted_text": "..."}],
#     "disclaimer": "..."}
```
