"""Pytest fixtures for the Mizizi backend.

Uses a dedicated test database (``mizizi_test``) created via the postgres
superuser, or falls back to a local SQLite file if unavailable. Tests run
against a fresh schema per session.
"""

import os
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import Base, engine, get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://mizizi:mizizi@localhost:5432/mizizi_test"
)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    if TEST_DATABASE_URL.startswith("postgres"):
        _ensure_test_database(TEST_DATABASE_URL)
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    # Re-read settings + rebuild engine against the test database.
    get_settings.cache_clear()
    from app.core import database as db_module

    db_module.engine.dispose()
    db_module.engine = db_module.create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    db_module.SessionLocal.configure(bind=db_module.engine)

    Base.metadata.drop_all(bind=db_module.engine)
    Base.metadata.create_all(bind=db_module.engine)

    # Seed reference data so tests have languages/communities/places.
    from app.seed.seed import seed_reference

    session = db_module.SessionLocal()
    try:
        seed_reference(session)
        session.commit()
    finally:
        session.close()

    yield
    db_module.engine.dispose()


def _ensure_test_database(url: str) -> None:
    host = "localhost"
    admin_user = os.environ.get("PG_SUPERUSER", "postgres")
    admin_pass = os.environ.get("PG_SUPERPASSWORD", "m@Trix549")
    import psycopg

    conn = psycopg.connect(f"host={host} user={admin_user} password={admin_pass} dbname=postgres")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'mizizi_test'")
        if cur.fetchone() is None:
            cur.execute("CREATE DATABASE mizizi_test OWNER mizizi")
    conn.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def reference_ids(client):
    langs = client.get("/api/v1/languages").json()
    communities = client.get("/api/v1/communities").json()
    places = client.get("/api/v1/places").json()
    return {
        "luganda": next(l for l in langs if l["iso_639_3"] == "lug")["id"],
        "english": next(l for l in langs if l["iso_639_3"] == "eng")["id"],
        "community": communities[0]["id"],
        "place": places[0]["id"],
    }


def _account(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def member(client, reference_ids):
    """A registered member whose cultural background covers the test
    reference data, so their recorded objects pass background validation."""
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "member@example.com",
            "password": "password123",
            "display_name": "Test Member",
            "language_ids": [reference_ids["luganda"], reference_ids["english"]],
            "place_ids": [reference_ids["place"]],
            "community_ids": [reference_ids["community"]],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return {
        "token": data["access_token"],
        "headers": _account(data["access_token"]),
        "user": data["user"],
    }


def _make_direct_user(db, email, role, **extra):
    from app.core import security
    from app.models import User

    user = User(
        email=email,
        password_hash=security.hash_password("password123"),
        display_name=extra.get("display_name"),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="session")
def admin(client, reference_ids):
    from app.core.database import SessionLocal
    from app.services import auth_service

    with SessionLocal() as db:
        user = _make_direct_user(db, "admin@example.com", "admin", display_name="Admin")
        token = auth_service.create_session(db, user)
    return {"token": token, "headers": _account(token), "user": user}


@pytest.fixture(scope="session")
def reviewer(client, reference_ids):
    from app.core.database import SessionLocal
    from app.services import auth_service

    with SessionLocal() as db:
        user = _make_direct_user(db, "reviewer@example.com", "reviewer", display_name="Reviewer")
        token = auth_service.create_session(db, user)
    return {"token": token, "headers": _account(token), "user": user}