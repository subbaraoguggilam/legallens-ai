"""Centralised configuration. All secrets come from environment variables."""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"  # development | production | test
    app_name: str = "LegalLens AI"

    # Database (SQLite for quick local runs, PostgreSQL + pgvector in docker-compose)
    database_url: str = "sqlite:///./data/legallens.db"

    # Auth
    secret_key: str = "dev-only-change-me-please-use-a-long-random-string"
    access_token_minutes: int = 60 * 12
    cookie_name: str = "ll_session"
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:3000"

    # Storage & encryption
    storage_dir: str = "./data/files"
    file_encryption_key: str = ""  # Fernet key; derived from secret_key in dev only

    # Upload limits
    max_upload_mb: int = 10
    max_pages: int = 200
    ocr_enabled: bool = True
    clamav_host: str = ""
    clamav_port: int = 3310

    # LLM provider: mock | gemini | groq
    llm_provider: str = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: float = 45.0
    redact_pii_for_llm: bool = True

    # Retrieval
    embedding_dim: int = 512
    retrieve_top_k: int = 5
    rerank_top_k: int = 3
    min_evidence_score: float = 0.5  # min share of question topic words found in evidence

    # Rate limits (requests per window)
    rate_limit_window_seconds: int = 60
    rate_limit_auth: int = 10
    rate_limit_ask: int = 20
    rate_limit_upload: int = 15
    rate_limit_default: int = 240

    disclaimer: str = (
        "This response explains information found in the provided documents. "
        "It is not a substitute for advice from a qualified legal professional."
    )

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def fernet_key(self) -> bytes:
        if self.file_encryption_key:
            return self.file_encryption_key.encode()
        # Development convenience only; production must set FILE_ENCRYPTION_KEY.
        return base64.urlsafe_b64encode(hashlib.sha256(self.secret_key.encode()).digest())

    def validate_for_production(self) -> None:
        if not self.is_production:
            return
        problems = []
        if self.secret_key.startswith("dev-only") or len(self.secret_key) < 32:
            problems.append("SECRET_KEY must be a random string of at least 32 characters")
        if not self.file_encryption_key:
            problems.append("FILE_ENCRYPTION_KEY must be set (Fernet key)")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true behind HTTPS")
        if problems:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
