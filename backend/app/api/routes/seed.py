"""Temporary seed route - remove after use."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db import get_db
from app.models import User

router = APIRouter()

@router.post("/api/seed-demo")
def seed_demo(db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == "demo@example.com"))
    if existing:
        return {"status": "already exists"}
    user = User(email="demo@example.com", password_hash=hash_password("DemoPassw0rd123"))
    db.add(user)
    db.commit()
    return {"status": "created"}
