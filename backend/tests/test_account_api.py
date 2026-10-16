from app import stremio
from app.accounts import ADDON, cmd_invite, cmd_revoke, stremio_key, user_for_token
from app.models import User
from app.stremio import StremioError


def no_tmdb(monkeypatch):
    monkeypatch.setattr("app.sync.tmdb.lookup", lambda imdb_id: None)


def test_connect_with_email_and_password(monkeypatch, db, client, ana):
    no_tmdb(monkeypatch)
    monkeypatch.setattr(stremio, "login", lambda email, password: "new-key")
    monkeypatch.setattr(stremio, "fetch_library", lambda key: [])
    body = {"email": "ana@example.com", "password": "secret"}
    response = client.post("/api/stremio/connect", json=body, headers=ana.headers)
    assert response.status_code == 200
    db.refresh(ana.user)
    assert stremio_key(ana.user) == "new-key"


def test_rejected_password_is_not_echoed(monkeypatch, client, ana):
    def refuse(email, password):
        raise StremioError("Wrong passphrase")

    monkeypatch.setattr(stremio, "login", refuse)
    body = {"email": "ana@example.com", "password": "my-secret-password"}
    response = client.post("/api/stremio/connect", json=body, headers=ana.headers)
    assert response.status_code == 400
    assert "my-secret-password" not in response.text


def test_connect_with_pasted_key_checks_it(monkeypatch, db, client, ana):
    no_tmdb(monkeypatch)
    calls = []
    monkeypatch.setattr(stremio, "fetch_library", lambda key: calls.append(key) or [])
    response = client.post("/api/stremio/connect", json={"auth_key": ' "pasted" '}, headers=ana.headers)
    assert response.status_code == 200
    assert calls[0] == "pasted"
    db.refresh(ana.user)
    assert stremio_key(ana.user) == "pasted"


def test_connect_changes_only_the_callers_account(monkeypatch, db, client, ana, bruno):
    no_tmdb(monkeypatch)
    monkeypatch.setattr(stremio, "fetch_library", lambda key: [])
    client.post("/api/stremio/connect", json={"auth_key": "k"}, headers=ana.headers)
    db.refresh(bruno.user)
    assert stremio_key(bruno.user) == "stremio-key-of-Bruno"


def test_disconnect(db, client, ana):
    assert client.delete("/api/stremio/connect", headers=ana.headers).status_code == 204
    db.refresh(ana.user)
    assert ana.user.stremio_auth_key is None
    assert client.get("/api/me", headers=ana.headers).json()["stremio_connected"] is False


def test_addon_link_works_and_old_links_keep_working(db, client, ana):
    link = client.post("/api/me/addon-link", headers=ana.headers).json()
    token = link["manifest_url"].split("/")[-2]
    assert user_for_token(db, ADDON, token).id == ana.user.id
    assert link["app_install_url"].startswith("stremio://")
    assert client.get(f"/{token}/manifest.json").status_code == 200
    assert client.get(f"/{ana.addon}/manifest.json").status_code == 200


def test_invite_and_revoke(db, client, capsys):
    cmd_invite(db, ["Carla"])
    link = [line for line in capsys.readouterr().out.split() if "#invite=" in line][0]
    token = link.split("#invite=")[1]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/me", headers=headers).json()
    assert me["name"] == "Carla" and me["via_invite"] is True
    assert me["has_password"] is False and me["stremio_connected"] is False

    cmd_revoke(db, [str(me["id"])])
    assert client.get("/api/me", headers=headers).status_code == 401
    assert db.get(User, me["id"]) is not None  # the account itself stays
