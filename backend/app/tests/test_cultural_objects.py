"""Tests for the Cultural Object lifecycle — the heart of Mizizi."""

import pytest


def _create_object(client, reference_ids, headers, **overrides):
    payload = {
        "object_type": "story",
        "title": "The Hare and the Lion (test)",
        "description": "A Luganda trickster tale.",
        "original_language_id": reference_ids["luganda"],
        "community_id": reference_ids["community"],
        "place_id": reference_ids["place"],
    }
    payload.update(overrides)
    resp = client.post("/api/v1/cultural-objects", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _creator_auth(obj, member):
    """Headers proving the caller is the object's creator (account + key)."""
    return {**member["headers"], "X-Creator-Key": obj["creator_key"]}


def _detail(client, object_id, member):
    resp = client.get(f"/api/v1/cultural-objects/{object_id}", headers=member["headers"])
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_object_generates_code(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    assert obj["object_code"].startswith("MZ-UG-LUG-STORY-")
    assert obj["object_code"].count("-") == 4
    assert obj["status"] == "draft"
    assert obj["visibility"] == "restricted"
    assert obj["creator_key"]  # the plaintext key is returned exactly once
    detail = _detail(client, obj["id"], member)
    assert detail["verification_status"] == "unverified"


def test_object_codes_are_unique_and_sequential(client, reference_ids, member):
    first = _create_object(client, reference_ids, member["headers"])
    second = _create_object(client, reference_ids, member["headers"])
    assert first["object_code"] != second["object_code"]
    n1 = int(first["object_code"].rsplit("-", 1)[1])
    n2 = int(second["object_code"].rsplit("-", 1)[1])
    assert n2 == n1 + 1


def test_create_object_creates_default_permissions_and_provenance(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    detail = _detail(client, obj["id"], member)
    assert len(detail["permissions"]) == 1
    assert detail["permissions"][0]["preservation"] is True
    assert detail["permissions"][0]["commercial_use"] is False
    assert any(e["event_type"] == "object_created" for e in detail["provenance_events"])


def test_upload_media_records_sha256_and_moves_to_processing(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/media",
        files={"file": ("recording.wav", b"\x00\x01\x02fakeaudio", "audio/wav")},
        headers=member["headers"],
    )
    assert resp.status_code == 201, resp.text
    media = resp.json()
    assert media["sha256_checksum"]
    assert media["media_type"] == "audio"
    detail = _detail(client, obj["id"], member)
    assert detail["status"] == "processing"


def test_media_is_immutable_and_streamable(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    upload = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/media",
        files={"file": ("a.wav", b"immutable-bytes", "audio/wav")},
        headers=member["headers"],
    ).json()
    stream = client.get(f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}", headers=member["headers"])
    assert stream.status_code == 200
    assert stream.content == b"immutable-bytes"


def _upload_audio(client, obj, member, data=b"playable-audio-bytes"):
    return client.post(
        f"/api/v1/cultural-objects/{obj['id']}/media",
        files={"file": ("recording.webm", data, "audio/webm")},
        headers=member["headers"],
    ).json()


def test_reviewer_can_stream_review_media_via_query_token(client, reference_ids, member, reviewer):
    """The review player must be able to hear the audio: the browser fetches a
    plain URL, so the reviewer's token is passed as a query parameter."""
    obj = _create_object(client, reference_ids, member["headers"])
    upload = _upload_audio(client, obj, member)
    assert obj["status"] == "draft"

    stream = client.get(
        f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}?token={reviewer['token']}"
    )
    assert stream.status_code == 200, stream.text
    assert stream.content == b"playable-audio-bytes"
    assert stream.headers["cache-control"] == "private, no-store"


def test_creator_can_stream_own_review_media_via_query_token(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    upload = _upload_audio(client, obj, member)
    stream = client.get(
        f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}?token={member['token']}"
    )
    assert stream.status_code == 200, stream.text


def test_anonymous_cannot_stream_review_media(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    upload = _upload_audio(client, obj, member)
    stream = client.get(f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}")
    assert stream.status_code == 403


def test_other_member_cannot_stream_review_media(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    upload = _upload_audio(client, obj, member)
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other-member@example.com",
            "password": "password123",
            "language_ids": [reference_ids["luganda"]],
            "place_ids": [reference_ids["place"]],
            "community_ids": [reference_ids["community"]],
        },
    )
    other_token = other.json()["access_token"]
    stream = client.get(
        f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}?token={other_token}"
    )
    assert stream.status_code == 403


def test_anonymous_can_stream_published_media(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    upload = _upload_audio(client, obj, member)
    _publish(client, reference_ids, member, obj)

    stream = client.get(f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}")
    assert stream.status_code == 200, stream.text
    assert stream.content == b"playable-audio-bytes"
    assert stream.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_media_range_requests_return_partial_content(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    data = b"0123456789abcdefghij"  # 20 bytes
    upload = _upload_audio(client, obj, member, data=data)
    url = f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}?token={member['token']}"

    stream = client.get(url, headers={"Range": "bytes=5-9"})
    assert stream.status_code == 206
    assert stream.content == b"56789"
    assert stream.headers["content-range"] == "bytes 5-9/20"
    assert stream.headers["accept-ranges"] == "bytes"
    assert stream.headers["content-length"] == "5"


def test_media_open_ended_range_and_invalid_range(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    upload = _upload_audio(client, obj, member, data=b"0123456789")
    url = f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}?token={member['token']}"

    suffix = client.get(url, headers={"Range": "bytes=-4"})
    assert suffix.status_code == 206
    assert suffix.content == b"6789"
    assert suffix.headers["content-range"] == "bytes 6-9/10"

    invalid = client.get(url, headers={"Range": "bytes=50-60"})
    assert invalid.status_code == 416
    assert invalid.headers["content-range"] == "bytes */10"


def test_octet_stream_audio_upload_gets_playable_content_type(client, reference_ids, member):
    """A .wav uploaded with a generic content type must still be served as
    audio so the browser will play it."""
    obj = _create_object(client, reference_ids, member["headers"])
    upload = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/media",
        files={"file": ("recording.wav", b"RIFF-fake-wav", "application/octet-stream")},
        headers=member["headers"],
    ).json()
    assert upload["media_type"] == "audio"
    stream = client.get(f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}")
    assert stream.status_code == 403  # still gated while in review
    stream = client.get(
        f"/api/v1/cultural-objects/{obj['id']}/media/{upload['id']}?token={member['token']}"
    )
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("audio/")


def test_transcription_and_human_review(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    tr = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions",
        json={"text": "Omwamukulu yalina amagezi.", "language_id": reference_ids["luganda"],
              "verification_status": "ai_processed"},
        headers=member["headers"],
    ).json()
    assert tr["verification_status"] == "ai_processed"

    reviewed = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions/{tr['id']}",
        json={"verification_status": "human_reviewed"},
        headers=member["headers"],
    ).json()
    assert reviewed["verification_status"] == "human_reviewed"

    detail = _detail(client, obj["id"], member)
    assert any(e["event_type"] == "transcription_reviewed" for e in detail["provenance_events"])
    # The object-level rollup must follow the transcription review.
    assert detail["verification_status"] == "human_reviewed"


def test_object_verification_status_rolls_up_with_human_review(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    client.post(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions",
        json={"text": "AI draft.", "verification_status": "ai_processed"},
        headers=member["headers"],
    )
    detail = _detail(client, obj["id"], member)
    assert detail["verification_status"] == "ai_processed"

    client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions/{detail['transcriptions'][0]['id']}",
        json={"verification_status": "human_reviewed"},
        headers=member["headers"],
    )
    detail = _detail(client, obj["id"], member)
    assert detail["verification_status"] == "human_reviewed"


def test_published_object_never_reports_unverified(client, reference_ids, member):
    """Regression: published objects used to display 'Verified: unverified'."""
    obj = _create_object(client, reference_ids, member["headers"])
    _upload_audio(client, obj, member)
    _publish(client, reference_ids, member, obj)
    detail = _detail(client, obj["id"], member)
    assert detail["status"] == "published"
    assert detail["verification_status"] == "human_reviewed"


def test_translation_linked_to_source(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    tr = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions",
        json={"text": "Omwamukulu yalina amagezi.", "language_id": reference_ids["luganda"]},
        headers=member["headers"],
    ).json()
    trans = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/translations",
        json={"source_transcription_id": tr["id"], "source_language_id": reference_ids["luganda"],
              "target_language_id": reference_ids["english"],
              "text": "The hare had wisdom."},
        headers=member["headers"],
    ).json()
    assert trans["source_transcription_id"] == tr["id"]
    assert trans["target_language"]["iso_639_3"] == "eng"


def test_derivative_refused_without_permission(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])  # default: derivative_work = False
    resp = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/derivatives",
        json={"derivative_type": "ai_adaptation", "content": "Adapted story."},
        headers=member["headers"],
    )
    assert resp.status_code == 403


def test_derivative_allowed_with_permission(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"derivative_work": True, "public_access": True},
        headers=_creator_auth(obj, member),
    )
    resp = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/derivatives",
        json={"derivative_type": "ai_adaptation", "title": "Kids' version", "content": "A simpler tale.",
              "model_name": "test-model"},
        headers=member["headers"],
    )
    assert resp.status_code == 201, resp.text
    derivative = resp.json()
    detail = _detail(client, obj["id"], member)
    assert any(d["id"] == derivative["id"] for d in detail["derivatives"])
    assert any(e["event_type"] == "derivative_created" for e in detail["provenance_events"])


def test_consent_recorded_and_traced(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.post(
        f"/api/v1/cultural-objects/{obj['id']}/consents",
        json={"consenting_party": "Community Elders — Masaka", "consent_type": "public_access"},
        headers=member["headers"],
    )
    assert resp.status_code == 201, resp.text
    detail = _detail(client, obj["id"], member)
    assert any(e["event_type"] == "consent_recorded" for e in detail["provenance_events"])


def test_publish_requires_public_access(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])

    # A bare draft is not publishable — the checklist must be met first.
    blocked = client.post(f"/api/v1/cultural-objects/{obj['id']}/publish", headers=member["headers"])
    assert blocked.status_code == 409
    assert "public_access" in blocked.text or "public access" in blocked.text

    # Direct PATCH to "published" must be gated the same way.
    bypass = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "published"},
        headers=member["headers"],
    )
    assert bypass.status_code == 409

    # Satisfy the checklist: verified status, human-reviewed transcript,
    # public-access permission and recorded consent.
    client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "verified"},
        headers=member["headers"],
    )
    client.post(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions",
        json={
            "text": "Once upon a time the hare and the lion...",
            "verification_status": "human_reviewed",
        },
        headers=member["headers"],
    )
    client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers=_creator_auth(obj, member),
    )
    client.post(
        f"/api/v1/cultural-objects/{obj['id']}/consents",
        json={"consenting_party": "Community Elders — Masaka", "consent_type": "public_access"},
        headers=member["headers"],
    )

    ok = client.post(f"/api/v1/cultural-objects/{obj['id']}/publish", headers=member["headers"])
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "published"
    assert any(e["event_type"] == "object_published" for e in ok.json()["provenance_events"])


def test_publish_check_reports_each_requirement(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.get(f"/api/v1/cultural-objects/{obj['id']}/publish-check", headers=member["headers"])
    assert resp.status_code == 200
    reqs = resp.json()["requirements"]
    keys = {r["requirement"] for r in reqs}
    assert keys == {
        "status_verified",
        "human_verification",
        "original_content",
        "public_access",
        "consent_recorded",
        "language_identified",
    }
    by_key = {r["requirement"]: r["satisfied"] for r in reqs}
    assert by_key["status_verified"] is False
    assert by_key["public_access"] is False
    assert by_key["language_identified"] is True  # helper sets Luganda


def test_withdraw_is_soft_delete(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "withdrawn"},
        headers=member["headers"],
    )
    assert resp.status_code == 200
    detail = _detail(client, obj["id"], member)
    assert detail["status"] == "withdrawn"
    assert any(e["event_type"] == "object_withdrawn" for e in detail["provenance_events"])


def test_invalid_status_rejected(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "not-a-status"},
        headers=member["headers"],
    )
    assert resp.status_code == 422


def _publish(client, reference_ids, member, obj):
    """Drive an object through the whole pipeline to published."""
    client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "verified"},
        headers=member["headers"],
    )
    client.post(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions",
        json={"text": "A verified tale.", "verification_status": "human_reviewed"},
        headers=member["headers"],
    )
    client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers=_creator_auth(obj, member),
    )
    client.post(
        f"/api/v1/cultural-objects/{obj['id']}/consents",
        json={"consenting_party": "Community Elders", "consent_type": "public_access"},
        headers=member["headers"],
    )
    resp = client.post(f"/api/v1/cultural-objects/{obj['id']}/publish", headers=member["headers"])
    assert resp.status_code == 200, resp.text


def test_search_finds_by_keyword_and_transcription(client, reference_ids, member):
    hare = _create_object(client, reference_ids, member["headers"], title="The Hare and the Lion (searchable)")
    _publish(client, reference_ids, member, hare)
    zebra = _create_object(client, reference_ids, member["headers"], title="Zebra Story")
    client.put(
        f"/api/v1/cultural-objects/{zebra['id']}/permissions",
        json={"public_access": True},
        headers=_creator_auth(zebra, member),
    )
    resp = client.get("/api/v1/search", params={"q": "hare"}, headers=member["headers"])
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert any("Hare" in (r["title"] or "") for r in results)
    # A non-published object never appears in archive search.
    assert not any(o["id"] == zebra["id"] for o in results)


def test_only_creator_can_grant_public_access(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])

    # No key → denied.
    no_key = client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers=member["headers"],
    )
    assert no_key.status_code == 403

    # Wrong key → denied.
    wrong_key = client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers={**member["headers"], "X-Creator-Key": "not-the-real-key"},
    )
    assert wrong_key.status_code == 403

    # Correct key → granted.
    ok = client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers=_creator_auth(obj, member),
    )
    assert ok.status_code == 200
    assert ok.json()["public_access"] is True

    # The provenance trail records the creator as the actor.
    detail = _detail(client, obj["id"], member)
    perm_event = [e for e in detail["provenance_events"] if e["event_type"] == "permission_changed"]
    assert perm_event and perm_event[-1]["actor"] == member["user"]["email"]


def test_creator_account_can_toggle_non_public_permissions(client, reference_ids, member):
    """The signed-in creator can tick boxes like derivative_work without the
    key — only public_access (the community's consent to be public) needs it."""
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"derivative_work": True, "educational_use": True},
        headers=member["headers"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["derivative_work"] is True
    assert body["educational_use"] is True
    assert body["public_access"] is False


def test_legacy_object_permissions_are_locked(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    # Wipe the creator credential (simulating a legacy/system object).
    from app.core.database import SessionLocal
    from app.models import CulturalObject as CO
    from sqlalchemy import update as sa_update

    with SessionLocal() as db:
        db.execute(sa_update(CO).where(CO.id == obj["id"]).values(creator_key_hash=None))
        db.commit()

    resp = client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers={**member["headers"], "X-Creator-Key": "whatever"},
    )
    assert resp.status_code == 403
    assert "no creator credential" in resp.text


def test_creator_can_revoke_public_access_without_key(client, reference_ids, member):
    """Granting public access needs the creator key; revoking it never does —
    the creator can always pull content back from their account."""
    obj = _create_object(client, reference_ids, member["headers"])
    ok = client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers=_creator_auth(obj, member),
    )
    assert ok.status_code == 200 and ok.json()["public_access"] is True, ok.text

    resp = client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": False},
        headers=member["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["public_access"] is False


def test_creator_can_drive_submission_to_publish(client, reference_ids, member):
    """The creator decides when their object enters review and when it goes live."""
    obj = _create_object(client, reference_ids, member["headers"])

    submit = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "processing"},
        headers=member["headers"],
    )
    assert submit.status_code == 200 and submit.json()["status"] == "processing", submit.text

    verified = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}/status",
        json={"status": "verified"},
        headers=member["headers"],
    )
    assert verified.status_code == 200 and verified.json()["status"] == "verified", verified.text

    client.post(
        f"/api/v1/cultural-objects/{obj['id']}/transcriptions",
        json={"text": "A verified tale.", "verification_status": "human_reviewed"},
        headers=member["headers"],
    )
    client.put(
        f"/api/v1/cultural-objects/{obj['id']}/permissions",
        json={"public_access": True},
        headers=_creator_auth(obj, member),
    )
    client.post(
        f"/api/v1/cultural-objects/{obj['id']}/consents",
        json={"consenting_party": "Community Elders", "consent_type": "public_access"},
        headers=member["headers"],
    )

    published = client.post(f"/api/v1/cultural-objects/{obj['id']}/publish", headers=member["headers"])
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "published"

    unrestricted = client.get(f"/api/v1/cultural-objects", headers=member["headers"]).json()
    assert any(o["id"] == obj["id"] and o["status"] == "published" for o in unrestricted["items"])


def test_non_public_objects_hidden_from_archive(client, reference_ids, member, reviewer):
    """Processing / withdrawn / verified-without-public-access objects never
    appear in the public archive or search — for anyone, including their
    creator — and are only reachable through the personal account."""
    processing = _create_object(client, reference_ids, member["headers"], title="In Processing")
    client.patch(
        f"/api/v1/cultural-objects/{processing['id']}/status",
        json={"status": "processing"},
        headers=member["headers"],
    )
    withdrawn = _create_object(client, reference_ids, member["headers"], title="Withdrawn One")
    client.patch(
        f"/api/v1/cultural-objects/{withdrawn['id']}/status",
        json={"status": "withdrawn"},
        headers=member["headers"],
    )
    verified_no_access = _create_object(
        client, reference_ids, member["headers"], title="Verified But Private"
    )
    client.patch(
        f"/api/v1/cultural-objects/{verified_no_access['id']}/status",
        json={"status": "verified"},
        headers=member["headers"],
    )

    archive = client.get("/api/v1/cultural-objects", headers=member["headers"]).json()
    archive_ids = {o["id"] for o in archive["items"]}
    assert not archive_ids.intersection({processing["id"], withdrawn["id"], verified_no_access["id"]})

    anonymous = client.get("/api/v1/cultural-objects").json()
    assert not {o["id"] for o in anonymous["items"]}.intersection(
        {processing["id"], withdrawn["id"], verified_no_access["id"]}
    )

    search = client.get("/api/v1/search", params={"q": "Processing"}, headers=member["headers"]).json()
    assert not any(o["id"] == processing["id"] for o in search["results"])

    # The creator still sees them from their personal account.
    mine = client.get("/api/v1/auth/me/objects", headers=member["headers"]).json()
    mine_ids = {o["id"]: o["status"] for o in mine}
    assert mine_ids[processing["id"]] == "processing"
    assert mine_ids[withdrawn["id"]] == "withdrawn"
    assert mine_ids[verified_no_access["id"]] == "verified"

    # A reviewer can only reach the review pipeline through the explicit queue
    # filter — not via the archive listing.
    reviewer_archive = client.get("/api/v1/cultural-objects", headers=reviewer["headers"]).json()
    assert processing["id"] not in {o["id"] for o in reviewer_archive["items"]}
    queue = client.get(
        "/api/v1/cultural-objects", params={"status": "processing"}, headers=reviewer["headers"]
    ).json()
    assert processing["id"] in {o["id"] for o in queue["items"]}


def test_relationships_knowledge_graph_seed(client, reference_ids, member):
    a = _create_object(client, reference_ids, member["headers"], title="Story A")
    b = _create_object(client, reference_ids, member["headers"], title="Story B")
    resp = client.post(
        f"/api/v1/cultural-objects/{a['id']}/relationships",
        json={"target_object_id": b["id"], "relationship_type": "variant_of"},
        headers=member["headers"],
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["target_object_code"] == b["object_code"]
    rels = client.get(
        f"/api/v1/cultural-objects/{a['id']}/relationships", headers=member["headers"]
    ).json()
    assert any(r["relationship_type"] == "variant_of" for r in rels)


def test_creator_can_edit_own_object(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}",
        json={"title": "The Hare and the Lion (edited)", "description": "A corrected tale."},
        headers=member["headers"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["title"] == "The Hare and the Lion (edited)"
    assert body["description"] == "A corrected tale."
    assert any(e["event_type"] == "status_changed" for e in body["provenance_events"])


def test_creator_edit_must_stay_in_background(client, reference_ids, member):
    obj = _create_object(client, reference_ids, member["headers"])
    langs = client.get("/api/v1/languages").json()
    other = next(l for l in langs if l["id"] != reference_ids["luganda"] and l["id"] != reference_ids["english"])
    resp = client.patch(
        f"/api/v1/cultural-objects/{obj['id']}",
        json={"original_language_id": other["id"]},
        headers=member["headers"],
    )
    assert resp.status_code == 422
    assert "not in your cultural background" in resp.json()["detail"]


def test_creator_can_delete_own_object(client, reference_ids, member):
    """A creator can permanently delete their own object — the archive's only
    destructive operation. The object and all its traces disappear."""
    obj = _create_object(client, reference_ids, member["headers"])
    resp = client.delete(f"/api/v1/cultural-objects/{obj['id']}", headers=member["headers"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["ok"] is True
    # The object is truly gone, not merely withdrawn.
    gone = client.get(f"/api/v1/cultural-objects/{obj['id']}", headers=member["headers"])
    assert gone.status_code == 404
    mine = client.get("/api/v1/auth/me/objects", headers=member["headers"]).json()
    assert not any(o["id"] == obj["id"] for o in mine)


def test_delete_requires_creator_or_admin(client, reference_ids, member, reviewer):
    """Reviewers cannot permanently delete; the creator's other accounts cannot
    delete an object they don't own."""
    obj = _create_object(client, reference_ids, member["headers"])

    # A reviewer cannot hard-delete.
    blocked = client.delete(
        f"/api/v1/cultural-objects/{obj['id']}", headers=reviewer["headers"]
    )
    assert blocked.status_code == 403

    # Anonymous cannot delete.
    anon = client.delete(f"/api/v1/cultural-objects/{obj['id']}")
    assert anon.status_code == 401