from app import stremio
from app.stremio import LibraryEntry, StremioError

SECRET = {"Authorization": "Bearer sync-secret-for-tests-0123456789"}


def fake_library(libraries):
    """Replace Stremio with a dict of auth key -> list of IMDb IDs (or an error)."""

    def fetch(auth_key):
        result = libraries[auth_key]
        if isinstance(result, Exception):
            raise result
        return [LibraryEntry(i, "movie", i, None, None, None) for i in result]

    return fetch


def test_sync_uses_each_users_own_library(monkeypatch, client, ana, bruno):
    monkeypatch.setattr("app.sync.tmdb.lookup", lambda imdb_id: None)
    monkeypatch.setattr(stremio, "fetch_library", fake_library({
        "stremio-key-of-Ana": ["tt0000001", "tt0000010"],
        "stremio-key-of-Bruno": ["tt0000002", "tt0000020"],
    }))
    response = client.post("/api/sync", headers=SECRET)
    assert response.status_code == 200
    assert [r["added"] for r in response.json()["users"]] == [1, 1]
    ana_ids = {t["imdb_id"] for t in client.get("/api/titles", headers=ana.headers).json()}
    assert ana_ids == {"tt0000001", "tt0000010"}


def test_one_users_failure_does_not_stop_the_others(monkeypatch, client, ana, bruno):
    monkeypatch.setattr("app.sync.tmdb.lookup", lambda imdb_id: None)
    monkeypatch.setattr(stremio, "fetch_library", fake_library({
        "stremio-key-of-Ana": StremioError("Session expired"),
        "stremio-key-of-Bruno": ["tt0000002", "tt0000020"],
    }))
    response = client.post("/api/sync", headers=SECRET)
    assert response.status_code == 502
    results = response.json()["users"]
    assert "error" in results[0] and results[1]["added"] == 1


def test_web_token_syncs_only_its_user(monkeypatch, client, ana, bruno):
    monkeypatch.setattr("app.sync.tmdb.lookup", lambda imdb_id: None)
    monkeypatch.setattr(stremio, "fetch_library", fake_library({
        "stremio-key-of-Ana": ["tt0000001"],
    }))
    response = client.post("/api/sync", headers=ana.headers)
    assert response.status_code == 200
    assert [r["user"] for r in response.json()["users"]] == [ana.user.id]


def test_sync_requires_a_token(client):
    assert client.post("/api/sync").status_code == 401
