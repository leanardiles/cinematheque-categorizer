from app.accounts import INVITE, WEB, add_token


def invite(db, account):
    token = add_token(db, account.user, WEB, INVITE)
    db.commit()
    return {"Authorization": f"Bearer {token}"}


def create_login(client, headers, email="ana@example.com", password="correct horse"):
    return client.post("/api/me/login", json={"email": email, "password": password}, headers=headers)


def test_invite_link_creates_a_login_and_then_stops_working(db, client, ana):
    headers = invite(db, ana)
    assert client.get("/api/me", headers=headers).json()["via_invite"] is True

    response = create_login(client, headers, email=" Ana@Example.com ")
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"
    session = {"Authorization": f"Bearer {response.json()['token']}"}

    assert client.get("/api/me", headers=headers).status_code == 401  # invite retired
    me = client.get("/api/me", headers=session).json()
    assert me["has_password"] is True and me["via_invite"] is False


def test_login_with_email_and_password(db, client, ana):
    create_login(client, invite(db, ana))
    response = client.post("/api/login", json={"email": "ANA@example.com", "password": "correct horse"})
    assert response.status_code == 200
    token = response.json()["token"]
    assert client.get("/api/me", headers={"Authorization": f"Bearer {token}"}).json()["name"] == "Ana"


def test_wrong_email_and_wrong_password_look_the_same(db, client, ana):
    create_login(client, invite(db, ana))
    wrong_password = client.post("/api/login", json={"email": "ana@example.com", "password": "nope"})
    wrong_email = client.post("/api/login", json={"email": "who@example.com", "password": "nope"})
    assert wrong_password.status_code == wrong_email.status_code == 401
    assert wrong_password.json() == wrong_email.json()


def test_repeated_failures_pause_logins(db, client, ana):
    create_login(client, invite(db, ana))
    for _ in range(5):
        client.post("/api/login", json={"email": "ana@example.com", "password": "nope"})
    paused = client.post("/api/login", json={"email": "ana@example.com", "password": "correct horse"})
    assert paused.status_code == 429


def test_logout_ends_only_that_session(db, client, ana):
    create_login(client, invite(db, ana))
    one = client.post("/api/login", json={"email": "ana@example.com", "password": "correct horse"}).json()
    two = client.post("/api/login", json={"email": "ana@example.com", "password": "correct horse"}).json()
    h1 = {"Authorization": f"Bearer {one['token']}"}
    h2 = {"Authorization": f"Bearer {two['token']}"}
    assert client.post("/api/logout", headers=h1).status_code == 204
    assert client.get("/api/me", headers=h1).status_code == 401
    assert client.get("/api/me", headers=h2).status_code == 200


def test_logout_keeps_the_original_token(client, ana):
    client.post("/api/logout", headers=ana.headers)
    assert client.get("/api/me", headers=ana.headers).status_code == 200


def test_changing_password_needs_the_current_one(db, client, ana):
    session = {"Authorization": f"Bearer {create_login(client, invite(db, ana)).json()['token']}"}
    body = {"email": "ana@example.com", "password": "a new password"}
    assert client.post("/api/me/login", json=body, headers=session).status_code == 400
    body["current_password"] = "correct horse"
    assert client.post("/api/me/login", json=body, headers=session).status_code == 200


def test_new_link_resets_a_forgotten_password(db, client, ana):
    create_login(client, invite(db, ana))
    body = {"email": "ana@example.com", "password": "remembered now"}
    assert client.post("/api/me/login", json=body, headers=invite(db, ana)).status_code == 200
    assert client.post("/api/login", json=body).status_code == 200


def test_email_must_be_unique(db, client, ana, bruno):
    create_login(client, invite(db, ana))
    response = create_login(client, invite(db, bruno), email="ana@example.com")
    assert response.status_code == 409


def test_short_password_rejected_without_echo(db, client, ana):
    response = create_login(client, invite(db, ana), password="short")
    assert response.status_code == 400 and "short" not in response.json()["detail"]
