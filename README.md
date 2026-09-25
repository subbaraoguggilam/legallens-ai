# LegalLens AI

An evidence-grounded legal document assistant that helps people understand,
compare and navigate legal documents in plain language — with clause-level
citations, risk indicators and actionable next steps.

> LegalLens AI provides legal information and document assistance. It is not
> intended to replace a qualified legal professional.

## What it does

- **Understand my document** — plain-language summary, parties, dates, major
  obligations, generated questions for a lawyer.
- **Ask questions about the document** — answers are generated only from
  retrieved clauses and always show the page/clause behind them; if the
  document doesn't say, the system says so instead of guessing.
- **Clause & risk scanner** — flags termination, payment, renewal, liability,
  confidentiality, IP, restrictive covenants, dispute resolution, jurisdiction,
  data/privacy, notice and refund clauses, without asserting anything is
  illegal.
- **Contract comparison** — side-by-side table (duration, notice, termination,
  payment, confidentiality, IP ownership, dispute resolution) with sources,
  presented without recommending which document to choose.
- **Next steps & lawyer-question checklist** — personalised to what was
  actually found in the document.
- **Evidence view** — every AI claim links back to the original page, with the
  quoted text highlighted.

See `LegalLens_AI_Project_Plan.pdf` (design doc, included in this repo) for the
full product/architecture specification this implementation follows.

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js 16 (App Router) + TypeScript + Tailwind CSS 4 |
| Backend | FastAPI + Python 3.12 |
| Database | PostgreSQL + pgvector (production/docker) or SQLite (local dev, no setup) |
| Extraction | PyMuPDF (PDF + OCR), python-docx |
| LLM | Pluggable: Gemini, Groq, or an offline deterministic mock (default) |
| Auth | JWT session cookie, bcrypt password hashing |

## Quick start — Docker Compose (recommended)

```bash
cp .env.example .env
# Generate real values for these two lines in .env:
python3 -c "import secrets; print(secrets.token_urlsafe(48))"          # -> SECRET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # -> FILE_ENCRYPTION_KEY

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API + docs: http://localhost:8000/docs

By default `LLM_PROVIDER=mock`, so the whole product — Q&A, summaries, risk
scanning, comparison — works immediately with **no API key**, using a
deterministic offline provider that only ever echoes back real evidence from
your document (never invented facts). Set `LLM_PROVIDER=gemini` or `groq` plus
the matching API key in `.env` to use a real model.

## Quick start — running locally without Docker

**Backend**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env   # or just export the two required vars
uvicorn app.main:app --reload --port 8000
```

SQLite is used automatically when `DATABASE_URL` isn't set to a PostgreSQL URL,
so no database setup is required for local development.

**Frontend**

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
npm run dev
```

Open http://localhost:3000, create an account, and upload a document. A sample
contract is provided at `samples/sample_employment_agreement.txt` for a quick
try, along with a second version for the comparison feature.

**Seed data (optional)**

```bash
cd backend
python3 ../database/seed.py
# creates demo@legallens.local / DemoPassw0rd123 with a sample document
```

## Running tests

```bash
cd backend
pip install -r requirements-dev.txt
ruff check app tests      # lint
pytest -q                 # unit, integration, security, rag, evaluation
pytest tests/evaluation -q -s   # prints measured retrieval accuracy & latency
```

All 58 backend tests pass as of this submission; the RAG evaluation suite
measures ~100% top-3 clause-retrieval accuracy and page accuracy on its labeled
question set, with sub-millisecond retrieval latency (see
`tests/evaluation/test_rag_evaluation.py` — these are measured, not asserted,
numbers).

```bash
cd frontend
npm install
npm run lint
npm run build
```

## Project structure

```
legallens/
├── frontend/          Next.js + TypeScript UI
├── backend/           FastAPI + Python API (see backend/README below)
├── database/          schema notes + seed script
├── docs/              architecture, security, API reference, threat model
├── samples/           sample documents to try the product with
├── docker-compose.yml
└── .env.example
```

Full details: [`docs/architecture.md`](docs/architecture.md) ·
[`docs/security.md`](docs/security.md) · [`docs/api.md`](docs/api.md) ·
[`docs/threat-model.md`](docs/threat-model.md) ·
[`database/schema.md`](database/schema.md).

## Design principles this build follows

- **Evidence over confidence.** Every factual claim about a document is
  generated from retrieved clauses only; the citation validator independently
  checks groundedness and downgrades or rejects claims it can't verify,
  regardless of what the model itself claims.
- **Untrusted documents.** Uploaded content is never treated as instructions —
  see the prompt-injection defence in `docs/security.md` and the passing test
  `tests/security/test_security.py::test_prompt_injection_in_document_is_not_obeyed`.
- **No fabricated evaluation metrics.** The numbers in this README and printed
  by the test suite are measured by running the code, not invented.
- **Legal information, not legal advice.** Every AI response carries a visible
  disclaimer; the system suggests professional review rather than predicting
  outcomes or telling the user what to do.
- **Works with zero configuration.** The mock LLM provider and SQLite default
  mean the whole product runs end-to-end with no API keys and no external
  database, which also keeps the automated test suite fast and deterministic.

## What this deliberately does not do

Per the design doc's "What Not to Build": this is not a generic chatbot bolted
onto an LLM, is not marketed as an AI lawyer, does not assert a clause is
illegal or unenforceable, does not hard-code one jurisdiction as universal, does
not expose documents publicly, and keeps all API keys out of source control
(`.env.example` contains no real secrets).

## License

MIT — see [`LICENSE`](LICENSE).
