"""Tests for accounts, authorization and the reviewer workflow."""

import pytest


def test_register_requires_cultural_background(client, reference_ids):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "nolang@example.com", "password": "password123"},
    )
    assert resp.status_code == 422
    assert "at least one language" in resp.json()["detail"]


def test_register_duplicate_email_conflicts(client, reference_ids):
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "language_ids": [reference_ids["luganda"]],
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_wrong_password_rejected(client, reference_ids):
    client.post(
        "/api/v1/auth/register",
        json={"email": "pass@example.com", "password": "password123",
              "language_ids": [reference_ids["luganda"]]},
    )
    bad = client.post("/api/v1/auth/login", json={"email": "pass@example.com", "password": "nope"})
    assert bad.status_code == 401
    ok = client.post("/api/v1/auth/login", json={"email": "pass@example.com", "password": "password123"})
    assert ok.status_code == 200
    assert ok.json()["user"]["role"] == "member"


def test_me_returns_profile_and_background(client, reference_ids):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@example.com",
            "password": "password123",
            "display_name": "Namara",
            "language_ids": [reference_ids["luganda"], reference_ids["english"]],
            "place_ids": [reference_ids["place"]],
            "community_ids": [reference_ids["community"]],
        },
    )
    token = resp.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["display_name"] == "Namara"
    assert {l["id"] for l in me["languages"]} == {reference_ids["luganda"], reference_ids["english"]}
    assert {p["id"] for p in me["places"]} == {reference_ids["place"]}
    assert {c["id"] for c in me["communities"]} == {reference_ids["community"]}


def test_create_object_requires_sign_in(client, reference_ids):
    resp = client.post(
        "/api/v1/cultural-objects",
        json={"object_type": "story", "title": "No auth"},
    )
    assert resp.status_code == 401


def test_create_object_enforces_background(client, reference_ids, member):
    resp = client.post(
        "/api/v1/cultural-objects",
        json={
            "object_type": "story",
            "title": "Out of my background",
            # No original_language → fine; use a language NOT in the member's
            # background by creating one first.
            "original_language_id": reference_ids["luganda"],
            "community_id": reference_ids["community"],
            "place_id": reference_ids["place"],
        },
        headers=member["headers"],
    )
    assert resp.status_code == 201, resp.text

    # A language outside the member's chosen background is rejected.
    langs = client.get("/api/v1/languages").json()
    other = next(l for l in langs if l["id"] != reference_ids["luganda"] and l["id"] != reference_ids["english"])
    resp = client.post(
        "/api/v1/cultural-objects",
        json={"object_type": "story", "title": "Wrong language",
              "original_language_id": other["id"]},
        headers=member["headers"],
    )
    assert resp.status_code == 422


def test_member_cannot_view_others_drafts(client, reference_ids, member):
    obj = _create(client, reference_ids, member["headers"])
    # A different member cannot see the draft.
    other = client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "password123",
              "language_ids": [reference_ids["luganda"]]},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    resp = client.get(f"/api/v1/cultural-objects/{obj['id']}", headers=other_headers)
    assert resp.status_code == 403


def test_review_queue_requires_reviewer(client, reference_ids, member):
    obj = _create(client, reference_ids, member["headers"])
    client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "processing"},
        headers=member["headers"],
    )
    # A plain member cannot list processing objects.
    blocked = client.get(
        "/api/v1/cultural-objects", params={"status": "processing"}, headers=member["headers"]
    )
    assert blocked.status_code == 403


def test_reviewer_sees_review_queue(client, reference_ids, member, reviewer):
    obj = _create(client, reference_ids, member["headers"])
    client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "processing"},
        headers=member["headers"],
    )
    queue = client.get(
        "/api/v1/cultural-objects", params={"status": "processing"}, headers=reviewer["headers"]
    )
    assert queue.status_code == 200
    assert any(o["id"] == obj["id"] for o in queue.json()["items"])


def test_public_archive_shows_only_published(client, reference_ids, member):
    draft = _create(client, reference_ids, member["headers"])
    published = _create(client, reference_ids, member["headers"], title="A public tale")
    # The publish checklist must be genuinely met to publish, so write the
    # status directly (as the seed does) — the gate is tested elsewhere.
    from app.core.database import SessionLocal
    from app.models import CulturalObject as CO
    from sqlalchemy import update as sa_update

    with SessionLocal() as db:
        db.execute(sa_update(CO).where(CO.id == published["id"]).values(status="published"))
        db.commit()
    # Anonymous visitor: only published objects appear.
    resp = client.get("/api/v1/cultural-objects")
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()["items"]]
    assert published["id"] in ids
    assert draft["id"] not in ids


def test_reviewer_application_flow(client, reference_ids, member, admin):
    # Member applies to become a reviewer.
    applied = client.post(
        "/api/v1/auth/apply-reviewer",
        json={"statement": "I am an elder fluent in Luganda and want to verify stories."},
        headers=member["headers"],
    )
    assert applied.status_code == 201
    app_id = applied.json()["id"]
    assert applied.json()["status"] == "pending"

    # Duplicate pending application is rejected.
    dup = client.post(
        "/api/v1/auth/apply-reviewer",
        json={"statement": "Let me in please."},
        headers=member["headers"],
    )
    assert dup.status_code == 409

    # A non-admin cannot list applications.
    blocked = client.get("/api/v1/auth/reviewer-applications", headers=member["headers"])
    assert blocked.status_code == 403

    # Admin approves; the member becomes a reviewer.
    apps = client.get("/api/v1/auth/reviewer-applications", headers=admin["headers"]).json()
    assert any(a["id"] == app_id for a in apps)
    decided = client.post(
        f"/api/v1/auth/reviewer-applications/{app_id}/decide",
        json={"approve": True},
        headers=admin["headers"],
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"

    me = client.get("/api/v1/auth/me", headers=member["headers"]).json()
    assert me["role"] == "reviewer"

    # Now they can access the review queue.
    queue = client.get(
        "/api/v1/cultural-objects", params={"status": "processing"}, headers=member["headers"]
    )
    assert queue.status_code == 200


def test_reviewer_cannot_apply_again(client, reference_ids, reviewer):
    resp = client.post(
        "/api/v1/auth/apply-reviewer",
        json={"statement": "I already am one."},
        headers=reviewer["headers"],
    )
    assert resp.status_code == 400


def test_anonymous_cannot_apply(client):
    resp = client.post("/api/v1/auth/apply-reviewer", json={"statement": "Let me in."})
    assert resp.status_code == 401


def test_my_objects_lists_own(client, reference_ids, member):
    mine = _create(client, reference_ids, member["headers"], title="Mine")
    resp = client.get("/api/v1/auth/me/objects", headers=member["headers"])
    assert resp.status_code == 200
    assert any(o["id"] == mine["id"] for o in resp.json())


def test_logout_revokes_session(client, reference_ids):
    token = client.post(
        "/api/v1/auth/register",
        json={"email": "logout@example.com", "password": "password123",
              "language_ids": [reference_ids["luganda"]]},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    out = client.post("/api/v1/auth/logout", headers=headers)
    assert out.status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def _create(client, reference_ids, headers, **overrides):
    payload = {
        "object_type": "story",
        "title": "Auth test object",
        "original_language_id": reference_ids["luganda"],
        "community_id": reference_ids["community"],
        "place_id": reference_ids["place"],
    }
    payload.update(overrides)
    resp = client.post("/api/v1/cultural-objects", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()