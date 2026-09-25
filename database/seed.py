"""Seed a demo user and a sample employment agreement for local development.

Usage (from backend/):
    python3 -m database.seed
or, from the repo root with the backend on PYTHONPATH:
    python3 database/seed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "DemoPassw0rd123"

SAMPLE_AGREEMENT = """EMPLOYMENT AGREEMENT

This Employment Agreement is made on 15 March 2025 between Acme Software Pvt Ltd \
(the "Employer") and Priya Rao (the "Employee").

1. Duration
1.1 This agreement shall continue for 2 year(s) from the start date unless terminated earlier.

8. Notice
8.1 Either party may terminate this agreement by providing sixty (60) days written notice.

9. Termination
9.1 The Employer may terminate this agreement immediately for cause, including gross misconduct.
9.2 Upon termination, the Employee must return all company property.

10. Confidentiality
10.1 The Employee shall keep confidential all proprietary information of the Employer \
during and after employment.

11. Intellectual Property
11.1 All work product and inventions created during employment shall be assigned to \
and owned by the Employer.

12. Restrictive Covenant
12.1 The Employee shall not compete with the Employer within the same industry for a \
period of 12 months after termination.

13. Payment
13.1 The Employer shall pay the Employee a monthly salary of Rs. 55,000.

14. Dispute Resolution
14.1 Any dispute arising from this agreement shall be resolved through arbitration in Hyderabad.
"""


def main() -> None:
    from sqlalchemy import select

    from app.core.security import hash_password
    from app.db import SessionLocal, init_db
    from app.models import User
    from app.services.pipeline import process_upload

    init_db()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print(f"Demo user already exists: {DEMO_EMAIL}")

        doc = process_upload(
            db, user.id, "sample_employment_agreement.txt", "text/plain", SAMPLE_AGREEMENT.encode()
        )
        print(f"Seeded sample document: {doc.id} ({doc.filename}, status={doc.status})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
