import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")

from app.core.security import (  # noqa: E402
    create_access_token,
    decode_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("Passw0rd123")
    assert verify_password("Passw0rd123", h)
    assert not verify_password("WrongPassword1", h)


def test_password_hash_is_salted():
    a = hash_password("Passw0rd123")
    b = hash_password("Passw0rd123")
    assert a != b


def test_weak_passwords_rejected():
    assert validate_password_strength("short1") is not None
    assert validate_password_strength("alllettersnodigits") is not None
    assert validate_password_strength("12345678901234") is not None
    assert validate_password_strength("GoodPass1234") is None


def test_access_token_roundtrip():
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_tampered_token_rejected():
    token = create_access_token("user-123")
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    assert decode_access_token(tampered) is None


def test_garbage_token_rejected():
    assert decode_access_token("not.a.jwt") is None
    assert decode_access_token("") is None
