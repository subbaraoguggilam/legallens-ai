# Security

This document summarises the controls implemented in the codebase and where to
find them. It complements `docs/threat-model.md`.

## Upload validation (`app/services/upload_validation.py`)

- Extension allow-list (pdf, docx, txt).
- Declared MIME type must match the extension.
- File signature check: PDFs must start with `%PDF-`; DOCX files must be a real
  ZIP archive containing `word/document.xml`; TXT must decode as UTF-8.
- Size limit (`MAX_UPLOAD_MB`, default 10 MB) enforced both at the API layer and
  in validation.
- Page-count limit (`MAX_PAGES`) enforced after extraction.
- Filenames are sanitised: path components, control characters and markup
  characters are stripped before the name is stored or ever echoed back to a
  browser (`sanitize_filename`).
- DOCX zip-bomb guard: rejects archives whose uncompressed size is implausibly
  large.

## Malware protection (`app/services/malware_scan.py`)

- Rejects the EICAR antivirus test string.
- Rejects PDFs containing active content markers (`/JavaScript`, `/JS`,
  `/Launch`, `/EmbeddedFile`, `/RichMedia`).
- Optionally scans every upload through ClamAV (`clamd` INSTREAM protocol) when
  `CLAMAV_HOST` is configured. If a scanner is configured but unreachable, the
  upload is rejected (fail closed), never silently allowed through.

## Private file access

- Original files are encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256)
  before being written to disk (`app/core/crypto.py`).
- Storage keys are never exposed to the client; only authenticated, owner-scoped
  API endpoints can read a document's content.
- The storage layer resolves paths within a fixed root and rejects any path that
  would escape it, defending against path traversal even if a caller passed a
  malicious key (`app/services/storage.py::_resolve`).

## Authentication & authorization

- Passwords are hashed with bcrypt (cost factor 12); a minimum-strength check
  requires at least 10 characters with letters and digits.
- Sessions are JWTs (HS256) stored in an `HttpOnly`, `SameSite=Lax` cookie;
  `COOKIE_SECURE` must be `true` in production (served over HTTPS).
- Every document-scoped endpoint depends on `get_owned_document`, which checks
  `document.user_id == current_user.id` and returns `404` (not `403`) on
  mismatch, so a non-owner cannot even confirm a document ID exists.

## Secrets

- All secrets (`SECRET_KEY`, `FILE_ENCRYPTION_KEY`, `GEMINI_API_KEY`,
  `GROQ_API_KEY`) are read from environment variables via `app/core/config.py`.
  None are hard-coded, and `.env` is git-ignored.
- `Settings.validate_for_production()` refuses to start in `ENV=production` with
  a default/short `SECRET_KEY`, a missing `FILE_ENCRYPTION_KEY`, or
  `COOKIE_SECURE=false`.

## Prompt injection protection (`app/ai/guardrails.py`)

Retrieved document text is treated as **untrusted data**, never instructions.
The system prompt establishes a strict authority order — system instructions,
then application instructions, then retrieved evidence, then the user's
question — and explicitly tells the model never to obey instructions found
inside evidence. As defence in depth, common injection phrasings ("ignore
previous instructions", "you are now a...", etc.) are stripped from evidence
text before it is sent to the model. See `tests/security/test_security.py::
test_prompt_injection_in_document_is_not_obeyed` for a working example.

## Privacy

- Documents are private to the owning account; there is no sharing feature.
- Users can delete a document (and, via cascade, its pages, chunks, analyses,
  conversations, messages and citations) or an individual conversation.
- PII patterns (emails, phone numbers, ID-shaped numbers) are redacted from
  evidence before it is sent to a third-party LLM provider
  (`REDACT_PII_FOR_LLM`, default on).
- Full document text is never written to logs; `app/core/logging.py` emits
  structured JSON with only operational metadata.

## Rate limiting (`app/core/rate_limit.py`)

A per-IP, per-endpoint-bucket sliding-window limiter protects `/api/auth/*`
(10/min), `/api/documents/{id}/ask` (20/min) and uploads (15/min) by default,
returning `429` with a `Retry-After` header. For multi-replica deployments,
back this with a shared store (e.g. Redis) behind the same interface, or
enforce limits at a reverse proxy.

## Transport & headers

- CORS is restricted to `CORS_ORIGINS` (comma-separated allow-list).
- Every response gets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
  and `Referrer-Policy: no-referrer`.
- Deploy behind HTTPS/TLS; `COOKIE_SECURE=true` requires it.

## What is intentionally not claimed

- The malware heuristics are not a substitute for a dedicated antivirus/sandbox
  in a real production deployment; ClamAV integration is provided but optional.
- The "groundedness" check in the citation validator is a lexical-overlap
  heuristic, not a trained entailment model; it catches obviously unsupported
  answers but is not a formal proof of correctness.
