"""Shared pytest fixtures: isolated DB + storage per test."""
from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("COOKIE_SECURE", "false")


@pytest.fixture()
def app_env(tmp_path, monkeypatch):
    """Fresh SQLite file + storage dir per test, with settings caches cleared."""
    db_path = tmp_path / "test.db"
    storage_dir = tmp_path / "files"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_DIR", str(storage_dir))

    from app.core.config import get_settings
    from app.core.rate_limit import reset_rate_limits
    from app.db import reset_engine

    get_settings.cache_clear()
    reset_engine()
    reset_rate_limits()
    yield
    reset_engine()
    get_settings.cache_clear()
    reset_rate_limits()


@pytest.fixture()
def client(app_env):
    from app.main import app

    with TestClient(app) as c:
        yield c


def unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def signup(client, password: str = "Passw0rd123") -> tuple[str, str]:
    email = unique_email()
    resp = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return email, password


SAMPLE_EMPLOYMENT_TXT = """EMPLOYMENT AGREEMENT

This Employment Agreement is made on 15 March 2025 between Acme Software Pvt Ltd (the "Employer") and Priya Rao (the "Employee").

1. Duration
1.1 This agreement shall continue for 2 year(s) from the start date unless terminated earlier.

8. Notice
8.1 Either party may terminate this agreement by providing sixty (60) days written notice.

9. Termination
9.1 The Employer may terminate this agreement immediately for cause, including gross misconduct.
9.2 Upon termination, the Employee must return all company property.

10. Confidentiality
10.1 The Employee shall keep confidential all proprietary information of the Employer during and after employment.

11. Intellectual Property
11.1 All work product and inventions created during employment shall be assigned to and owned by the Employer.

12. Restrictive Covenant
12.1 The Employee shall not compete with the Employer within the same industry for a period of 12 months after termination.

13. Payment
13.1 The Employer shall pay the Employee a monthly salary of Rs. 55,000.

14. Dispute Resolution
14.1 Any dispute arising from this agreement shall be resolved through arbitration in Hyderabad.
"""

SAMPLE_EMPLOYMENT_TXT_B = """EMPLOYMENT AGREEMENT

This Employment Agreement is made on 1 June 2025 between Beta Corp (the "Employer") and Rahul Singh (the "Employee").

1. Duration
1.1 This agreement shall continue for 1 year(s) from the start date unless terminated earlier.

8. Notice
8.1 Either party may terminate this agreement by providing thirty (30) days written notice.

11. Intellectual Property
11.1 All work product shall be jointly owned by the Employer and Employee.

13. Payment
13.1 The Employer shall pay the Employee a monthly salary of Rs. 50,000.

14. Dispute Resolution
14.1 Any dispute arising from this agreement shall be resolved in the courts of Bengaluru.
"""


def upload_sample(client, text: str = SAMPLE_EMPLOYMENT_TXT, filename: str = "sample.txt") -> dict:
    resp = client.post(
        "/api/documents",
        files={"file": (filename, text.encode(), "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
