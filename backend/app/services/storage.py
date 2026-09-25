"""Private encrypted file storage. Paths are never exposed to clients."""
from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.crypto import decrypt_bytes, encrypt_bytes


def _resolve(storage_key: str) -> Path:
    root = get_settings().storage_path.resolve()
    path = (root / storage_key).resolve()
    if root not in path.parents:  # defence in depth against traversal
        raise ValueError("Invalid storage key")
    return path


def save_encrypted(user_id: str, data: bytes) -> str:
    key = f"{user_id}/{uuid.uuid4().hex}.bin"
    path = _resolve(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encrypt_bytes(data))
    return key


def load_decrypted(storage_key: str) -> bytes:
    return decrypt_bytes(_resolve(storage_key).read_bytes())


def delete_file(storage_key: str) -> None:
    try:
        _resolve(storage_key).unlink(missing_ok=True)
    except ValueError:
        pass
