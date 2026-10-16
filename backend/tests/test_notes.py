def patch(client, account, body, title=None):
    title_id = (title or account.title).id
    return client.patch(f"/api/titles/{title_id}", json=body, headers=account.headers)


def test_add_edit_and_clear_a_note(client, ana):
    response = patch(client, ana, {"note": "  Recommended   by Bruno  "})
    assert response.status_code == 200
    assert response.json()["note"] == "Recommended by Bruno"  # spaces tidied
    assert response.json()["name"] == "Ana's film"  # name untouched

    assert patch(client, ana, {"note": "Palme d'Or"}).json()["note"] == "Palme d'Or"
    assert patch(client, ana, {"note": ""}).json()["note"] is None


def test_renaming_keeps_the_note(client, ana):
    patch(client, ana, {"note": "Recommended by Bruno"})
    response = patch(client, ana, {"name": "New name"})
    assert response.json()["note"] == "Recommended by Bruno"


def test_note_limit_is_120_characters(client, ana):
    assert patch(client, ana, {"note": "x" * 120}).status_code == 200
    assert patch(client, ana, {"note": "x" * 121}).status_code == 422


def test_cannot_note_another_users_film(client, ana, bruno):
    assert patch(client, ana, {"note": "mine"}, title=bruno.title).status_code == 404


def test_search_matches_notes(client, ana):
    patch(client, ana, {"note": "Recommended by Bruno"})
    found = client.get("/api/titles", params={"q": "bruno"}, headers=ana.headers).json()
    assert [t["imdb_id"] for t in found] == ["tt0000001"]


def test_note_is_the_first_entry_on_the_films_page_in_stremio(client, ana):
    patch(client, ana, {"note": "Recommended by Bruno, watch it on the big screen"})
    streams = client.get(f"/{ana.addon}/stream/movie/tt0000001.json").json()["streams"]
    first = streams[0]["description"].split("\n")
    assert first[0].startswith("📝 Recommended")
    assert all(len(line) <= 30 for line in first)
    assert "/detail/movie/tt0000001" in streams[0]["externalUrl"]


def test_no_note_no_entry(client, ana):
    streams = client.get(f"/{ana.addon}/stream/movie/tt0000001.json").json()["streams"]
    assert not any(s["description"].startswith("📝") for s in streams)
