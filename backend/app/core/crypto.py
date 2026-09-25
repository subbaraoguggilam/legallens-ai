"""Encryption at rest for uploaded files (Fernet: AES-128-CBC + HMAC-SHA256)."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _fernet() -> Fernet:
    return Fernet(get_settings().fernet_key())


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return _fernet().decrypt(token)
    except InvalidToken as exc:  # wrong key or tampered file
        raise ValueError("Stored file could not be decrypted") from exc
