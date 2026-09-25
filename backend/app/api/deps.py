"""Shared FastAPI dependencies: DB session and the authenticated user."""
from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db import get_db
from app.models import Document, User


def get_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias="ll_session"),
) -> User:
    settings = get_settings()
    token = session_token
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    del settings  # reserved for future cookie-name customisation
    return user


def get_owned_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Document:
    """Authorization: only the owning user may access their document."""
    doc = db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        # 404, not 403: don't reveal whether a document id exists to non-owners.
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc
