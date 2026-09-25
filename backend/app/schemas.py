"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    document_type: str
    status: str
    error: str | None = None
    page_count: int
    size_bytes: int
    warnings: list[str] = []
    created_at: datetime


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = None


class CitationOut(BaseModel):
    document_id: str
    page: int
    clause: str | None = None
    quoted_text: str


class AskResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    confidence: str
    citations: list[CitationOut]
    disclaimer: str


class SummaryResponse(BaseModel):
    document_id: str
    document_type: str
    summary: str
    parties: list[str]
    dates: list[str]
    obligations: list[str]
    disclaimer: str


class RiskFindingOut(BaseModel):
    category: str
    page: int
    clause: str | None
    section: str | None
    snippet: str
    needs_attention: bool


class RiskScanResponse(BaseModel):
    document_id: str
    findings: list[RiskFindingOut]
    categories_found: list[str]
    review_note: str
    disclaimer: str


class ChecklistResponse(BaseModel):
    document_id: str
    your_situation: list[dict]
    next_steps: list[str]
    questions_for_a_lawyer: list[str]
    disclaimer: str


class CompareRequest(BaseModel):
    document_id_a: str
    document_id_b: str


class EvidencePageOut(BaseModel):
    document_id: str
    page: int
    page_count: int
    text: str
