"""Tests for the admin console and the creator-key escrow/recovery flow."""


def _create(client, reference_ids, headers, **overrides):
    payload = {
        "object_type": "story",
        "title": "Admin test object",
        "original_language_id": reference_ids["luganda"],
        "community_id": reference_ids["community"],
        "place_id": reference_ids["place"],
    }
    payload.update(overrides)
    resp = client.post("/api/v1/cultural-objects", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_admin_endpoints_require_admin(client, reference_ids, member, admin):
    for method, path in [
        ("get", "/admin/users"),
        ("get", "/admin/objects"),
        ("get", "/admin/creator-keys"),
        ("get", "/admin/creator-key-requests"),
    ]:
        anon = getattr(client, method)(f"/api/v1{path}")
        assert anon.status_code == 401, path
        member_resp = getattr(client, method)(f"/api/v1{path}", headers=member["headers"])
        assert member_resp.status_code == 403, path
        admin_resp = getattr(client, method)(f"/api/v1{path}", headers=admin["headers"])
        assert admin_resp.status_code == 200, path


def test_admin_lists_users_with_their_objects(client, reference_ids, member, admin):
    obj = _create(client, reference_ids, member["headers"], title="Visible to admin")
    users = client.get("/api/v1/admin/users", headers=admin["headers"]).json()
    me = next(u for u in users["items"] if u["id"] == member["user"]["id"])
    assert me["email"] == member["user"]["email"]
    assert any(o["id"] == obj["id"] and o["title"] == "Visible to admin" for o in me["objects"])


def test_admin_can_delete_any_object(client, reference_ids, member, admin):
    obj = _create(client, reference_ids, member["headers"])
    resp = client.delete(f"/api/v1/admin/objects/{obj['id']}", headers=admin["headers"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["ok"] is True
    gone = client.get(f"/api/v1/cultural-objects/{obj['id']}", headers=member["headers"])
    assert gone.status_code == 404


def test_creator_key_is_escrowed_with_admin(client, reference_ids, member, admin):
    obj = _create(client, reference_ids, member["headers"])
    ledger = client.get("/api/v1/admin/creator-keys", headers=admin["headers"]).json()
    row = next(e for e in ledger if e["cultural_object_id"] == obj["id"])
    assert row["object_code"] == obj["object_code"]
    assert row["user_email"] == member["user"]["email"]
    # The plaintext key is held by the administrator for recovery.
    assert row["key"] == obj["creator_key"]


def test_creator_key_request_and_issue_flow(client, reference_ids, member, admin):
    obj = _create(client, reference_ids, member["headers"])

    # Only the creator can request their key.
    other = client.post(
        "/api/v1/auth/register",
        json={"email": "otherkey@example.com", "password": "password123",
              "language_ids": [reference_ids["luganda"]]},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    denied = client.post(
        "/api/v1/creator-keys/requests",
        json={"object_id": obj["id"]},
        headers=other_headers,
    )
    assert denied.status_code == 403

    # The creator requests the key; it lands in the admin queue.
    requested = client.post(
        "/api/v1/creator-keys/requests",
        json={"object_id": obj["id"]},
        headers=member["headers"],
    )
    assert requested.status_code == 201, requested.text
    request_id = requested.json()["id"]
    assert requested.json()["status"] == "pending"

    # Duplicate pending request is rejected.
    dup = client.post(
        "/api/v1/creator-keys/requests",
        json={"object_id": obj["id"]},
        headers=member["headers"],
    )
    assert dup.status_code == 409

    # The user sees their request; the admin sees it in the queue.
    mine = client.get("/api/v1/creator-keys/requests", headers=member["headers"]).json()
    assert any(r["id"] == request_id for r in mine)

    queue = client.get("/api/v1/admin/creator-key-requests", headers=admin["headers"]).json()
    assert any(r["id"] == request_id for r in queue)

    # Admin issues the key (delivered to the requester's email). Console backend
    # logs rather than relays, but the request is closed and marked sent.
    issued = client.post(
        f"/api/v1/admin/creator-key-requests/{request_id}/issue",
        headers=admin["headers"],
    )
    assert issued.status_code == 200, issued.text
    assert issued.json()["status"] == "sent"

    queue = client.get("/api/v1/admin/creator-key-requests", headers=admin["headers"]).json()
    assert not any(r["id"] == request_id for r in queue)


def test_admin_can_decline_key_request(client, reference_ids, member, admin):
    obj = _create(client, reference_ids, member["headers"])
    requested = client.post(
        "/api/v1/creator-keys/requests",
        json={"object_id": obj["id"]},
        headers=member["headers"],
    ).json()
    declined = client.post(
        f"/api/v1/admin/creator-key-requests/{requested['id']}/decline",
        headers=admin["headers"],
    )
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"

    # A declined request can be re-requested later.
    again = client.post(
        "/api/v1/creator-keys/requests",
        json={"object_id": obj["id"]},
        headers=member["headers"],
    )
    assert again.status_code == 201
