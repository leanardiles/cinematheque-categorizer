"""One user's token must never read or change another user's data."""


def test_api_lists_only_own_collections(client, ana, bruno):
    names = [c["name"] for c in client.get("/api/collections", headers=ana.headers).json()]
    assert names == ["French"]


def test_api_cannot_touch_other_users_collection(client, ana, bruno):
    url = f"/api/collections/{bruno.collection.id}"
    assert client.get(f"{url}/titles", headers=ana.headers).status_code == 404
    assert client.patch(url, json={"name": "Mine"}, headers=ana.headers).status_code == 404
    assert client.delete(url, headers=ana.headers).status_code == 404
    response = client.post(f"{url}/titles", json={"title_id": ana.title.id}, headers=ana.headers)
    assert response.status_code == 404


def test_api_lists_only_own_titles(client, ana, bruno):
    titles = client.get("/api/titles", headers=ana.headers).json()
    assert [t["imdb_id"] for t in titles] == ["tt0000001"]


def test_addon_manifest_is_per_user(client, ana, bruno):
    ana_names = [c["name"] for c in client.get(f"/{ana.addon}/manifest.json").json()["catalogs"]]
    assert "French Cinematheque" in ana_names
    assert "Horror Cinematheque" not in ana_names
    assert client.get("/wrong-token/manifest.json").status_code == 404


def test_addon_catalog_cannot_read_other_users_collection(client, ana, bruno):
    url = f"/{ana.addon}/catalog/movie/collection-{bruno.collection.id}.json"
    assert client.get(url).json() == {"metas": []}


def test_addon_action_cannot_file_into_other_users_collection(db, client, ana, bruno):
    url = (
        f"/{ana.addon}/do/add/{bruno.collection.id}/{ana.title.imdb_id}"
        "/catalog/movie/cinematheque-actions.json"
    )
    assert client.get(url).json() == {"metas": []}
    titles = client.get(f"/api/collections/{bruno.collection.id}/titles", headers=bruno.headers)
    assert [t["imdb_id"] for t in titles.json()] == ["tt0000002"]


def test_addon_action_files_own_film(client, ana):
    other = client.post("/api/collections", json={"name": "Later"}, headers=ana.headers).json()
    url = f"/{ana.addon}/do/add/{other['id']}/tt0000001/catalog/movie/cinematheque-actions.json"
    assert client.get(url).json()["metas"][0]["name"].startswith("✓ Added to Later")
