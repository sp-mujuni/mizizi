"""Tests for reference data (languages, communities, places, contributors)."""


def test_languages_seeded(client):
    resp = client.get("/api/v1/languages")
    assert resp.status_code == 200
    langs = resp.json()
    codes = {l["iso_639_3"] for l in langs}
    assert {"lug", "nyn", "ach", "eng"}.issubset(codes)


def test_communities_seeded(client):
    resp = client.get("/api/v1/communities")
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()}
    assert {"Baganda", "Banyankore", "Acholi"}.issubset(names)


def test_places_seeded(client):
    resp = client.get("/api/v1/places")
    assert resp.status_code == 200
    assert len(resp.json()) >= 5


def test_contributor_crud(client):
    created = client.post(
        "/api/v1/contributors",
        json={"display_name": "Test Collector", "anonymous": False, "role": "researcher"},
    )
    assert created.status_code == 201, created.text
    cid = created.json()["id"]
    updated = client.patch(
        f"/api/v1/contributors/{cid}", json={"role": "senior researcher"}
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "senior researcher"


def test_language_unique_constraint(client):
    resp = client.post("/api/v1/languages", json={"name": "Luganda"})
    assert resp.status_code in (409, 500)