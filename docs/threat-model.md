# Threat Model

A lightweight STRIDE-style pass over LegalLens AI's main assets: uploaded
documents, account credentials, and the integrity of AI answers.

## Assets

1. **Uploaded documents** — often sensitive (employment terms, salary, personal
   data). Confidentiality and integrity matter most.
2. **Account credentials / sessions** — protect access to (1).
3. **AI answers and citations** — must not mislead the user into believing an
   unsupported claim is a fact from their document.
4. **The service itself** — availability against abuse (rate limiting).

## Threats and mitigations

| # | Threat | Mitigation |
| --- | --- | --- |
| 1 | Attacker uploads a malicious file (malware, zip bomb, PDF with embedded scripts) to compromise the server or other users | Extension/MIME/signature validation, malware heuristics + optional ClamAV, DOCX zip-bomb size cap, sandboxed extraction library (PyMuPDF/python-docx, no shell-out) |
| 2 | Attacker guesses or enumerates document IDs to read another user's document | Every document route requires ownership via `get_owned_document`; mismatches return `404`, not `403`, so existence isn't confirmed either |
| 3 | Path traversal via a crafted filename or storage key | Filenames are sanitised before storage; the storage layer resolves and validates paths stay under its root directory |
| 4 | Credential stuffing / brute-force login | bcrypt hashing (slow by design), per-IP rate limiting on `/api/auth/*`, minimum password strength |
| 5 | Session hijacking via XSS reading a token from JS-accessible storage | Session token is an `HttpOnly` cookie, never exposed to JavaScript; `SameSite=Lax`; `Secure` required in production |
| 6 | A malicious or compromised document tries to hijack the AI ("prompt injection") to exfiltrate the system prompt, mislabel evidence, or make the model claim something the document doesn't say | Document text is architecturally separated as untrusted evidence; the system prompt defines a strict authority order and instructs the model never to obey text found in evidence; injection-phrase stripping as defence in depth; the evidence validator independently checks that any "document_supported" claim is actually grounded before returning it, regardless of what the model claims |
| 7 | LLM hallucinates a fact not present in the document | RAG scopes generation to retrieved chunks only; the citation validator downgrades ungrounded "document_supported" answers to "professional_review_recommended"; empty/low-coverage retrieval short-circuits to "insufficient_evidence" without calling the LLM at all |
| 8 | Sensitive personal data (emails, phone numbers, ID numbers) leaked to a third-party LLM provider | PII redaction pass on evidence before it is sent to Gemini/Groq (`REDACT_PII_FOR_LLM`) |
| 9 | Denial of service via large uploads or high-frequency requests | Upload size cap enforced at the HTTP layer before the body is fully buffered; per-bucket rate limiting on auth, ask and upload endpoints |
| 10 | Secrets leaked via source control or error messages | All secrets come from environment variables (never hard-coded); `.env` is git-ignored; the global exception handler returns a generic message and logs details server-side only |
| 11 | Data retained longer than the user wants | Users can delete a document (cascading to all derived data) or a single conversation at any time |
| 12 | SQL injection | SQLAlchemy's parameterised query builder is used throughout; no raw string-interpolated SQL exists in the codebase |
| 13 | Stored XSS via a document's filename or extracted content rendered in the frontend | Filenames are sanitised server-side (control/markup characters stripped); the frontend renders all user-controlled text through React's default escaping (no `dangerouslySetInnerHTML` is used) |

## Explicitly out of scope for this submission

- Multi-tenant organisation/team sharing (not part of the design doc's MVP).
- A dedicated WAF or DDoS mitigation layer (assumed to sit in front of this
  service in a real deployment, e.g. at a cloud load balancer).
- Formal penetration testing; `tests/security/` covers the concrete threats
  above with automated tests but is not a substitute for an external audit.
