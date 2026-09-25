"""RAG orchestration: query analysis -> retrieval -> evidence -> LLM -> validation."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ai.citation_validator import ValidatedAnswer, validate
from app.ai.guardrails import SYSTEM_INSTRUCTIONS, build_user_prompt
from app.ai.providers import LLMError, get_provider
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.retrieval import rerank, retrieve

log = get_logger("rag")

GREETING_WORDS = {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay"}


@dataclass
class QueryPlan:
    kind: str  # "greeting" | "document_question"
    normalized: str


def classify_query(question: str) -> QueryPlan:
    q = question.strip().lower().rstrip("!.")
    if q in GREETING_WORDS or len(q) < 2:
        return QueryPlan("greeting", q)
    return QueryPlan("document_question", question.strip())


def _parse_json(raw: str) -> dict:
    import json
    import re

    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning("llm_json_parse_failed")
        return {}


async def answer_question(db: Session, document_id: str, question: str) -> ValidatedAnswer:
    plan = classify_query(question)
    if plan.kind == "greeting":
        return ValidatedAnswer(
            "Hi! Ask me anything about this document — for example, its notice period, "
            "payment terms or termination clauses — and I'll answer using the document's own text.",
            "general_information",
            [],
        )

    s = get_settings()
    candidates = retrieve(db, document_id, plan.normalized, top_k=s.retrieve_top_k)
    top = rerank(plan.normalized, candidates, top_n=s.rerank_top_k)

    if not top or top[0].coverage < s.min_evidence_score:
        return ValidatedAnswer(
            "The uploaded document does not appear to contain evidence that answers this "
            "question. Try rephrasing, or ask about a specific clause or topic in the document.",
            "insufficient_evidence",
            [],
        )

    evidence = [
        {"index": i, "page": r.chunk.page_number, "clause": r.chunk.clause, "text": r.chunk.content}
        for i, r in enumerate(top)
    ]
    prompt = build_user_prompt(plan.normalized, evidence)

    try:
        raw_text = await get_provider().generate(SYSTEM_INSTRUCTIONS, prompt)
    except LLMError as exc:
        log.error("llm_generation_failed", extra={"ctx": {"error": str(exc)}})
        return ValidatedAnswer(
            "The AI assistant is temporarily unavailable. Please try again shortly.",
            "insufficient_evidence",
            [],
        )

    parsed = _parse_json(raw_text)
    return validate(parsed, top)
