"""Pluggable LLM provider abstraction (design doc section 4).

Set LLM_PROVIDER=gemini|groq|mock in the environment. Application code only ever
calls `get_provider().generate(...)`, so swapping providers changes no other file.
"""
from __future__ import annotations

import json
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("llm")


class LLMError(RuntimeError):
    """Raised when a provider cannot produce a response."""


class LLMProvider(Protocol):
    async def generate(self, system: str, prompt: str) -> str: ...


class GeminiProvider:
    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key, self.model, self.timeout = api_key, model, timeout

    async def generate(self, system: str, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=body)
        if resp.status_code >= 400:
            log.error("gemini_error", extra={"ctx": {"status": resp.status_code}})
            raise LLMError(f"Gemini request failed ({resp.status_code}).")
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise LLMError("Gemini returned an unexpected response shape.") from exc


class GroqProvider:
    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key, self.model, self.timeout = api_key, model, timeout

    async def generate(self, system: str, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        body = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=body, headers=headers)
        if resp.status_code >= 400:
            log.error("groq_error", extra={"ctx": {"status": resp.status_code}})
            raise LLMError(f"Groq request failed ({resp.status_code}).")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError("Groq returned an unexpected response shape.") from exc


class MockProvider:
    """Deterministic offline provider used for local runs, demos and tests.

    It never invents document facts: it echoes back only the evidence it was
    given, in the same JSON contract a real provider must follow.
    """

    async def generate(self, system: str, prompt: str) -> str:
        try:
            payload = json.loads(prompt.rsplit("EVIDENCE_JSON:", 1)[-1])
        except (json.JSONDecodeError, IndexError):
            payload = {}
        question = payload.get("question", "")
        evidence = payload.get("evidence", [])
        if not evidence:
            return json.dumps(
                {
                    "answer": (
                        "The uploaded document does not contain evidence that answers this "
                        "question."
                    ),
                    "confidence": "insufficient_evidence",
                    "citation_indices": [],
                }
            )
        lead = evidence[0]
        cite_line = ", ".join(
            f"clause {e['clause']}" if e.get("clause") else f"page {e['page']}" for e in evidence[:3]
        )
        answer = (
            f"Based on the uploaded document, the relevant provisions are found in {cite_line}. "
            f"{lead['text'][:280].rstrip()}"
        )
        return json.dumps(
            {
                "answer": answer,
                "confidence": "document_supported",
                "citation_indices": list(range(min(3, len(evidence)))),
                "_note": f"mock provider echo for: {question[:120]}",
            }
        )


def get_provider() -> LLMProvider:
    s = get_settings()
    if s.llm_provider == "gemini":
        if not s.gemini_api_key:
            raise LLMError("GEMINI_API_KEY is not configured.")
        return GeminiProvider(s.gemini_api_key, s.gemini_model, s.llm_timeout_seconds)
    if s.llm_provider == "groq":
        if not s.groq_api_key:
            raise LLMError("GROQ_API_KEY is not configured.")
        return GroqProvider(s.groq_api_key, s.groq_model, s.llm_timeout_seconds)
    return MockProvider()
