from datetime import datetime, timezone

from app.accounts import ADDON, WEB, hash_token, stremio_key, user_for_token
from app.models import UserToken


def test_tokens_are_stored_hashed(db, ana):
    hashes = set(db.scalars(UserToken.__table__.select().with_only_columns(UserToken.token_hash)))
    assert hash_token(ana.web) in hashes
    assert ana.web not in hashes


def test_token_kinds_are_not_interchangeable(db, ana):
    assert user_for_token(db, WEB, ana.web).id == ana.user.id
    assert user_for_token(db, ADDON, ana.web) is None
    assert user_for_token(db, WEB, ana.addon) is None


def test_revoked_token_is_rejected(db, client, ana):
    row = db.query(UserToken).filter_by(token_hash=hash_token(ana.web)).one()
    row.revoked_at = datetime.now(timezone.utc)
    db.commit()
    assert client.get("/api/me", headers=ana.headers).status_code == 401


def test_stremio_key_is_encrypted(db, ana):
    assert ana.user.stremio_auth_key != "stremio-key-of-Ana"
    assert stremio_key(ana.user) == "stremio-key-of-Ana"


def test_me_identifies_the_user(client, ana, bruno):
    assert client.get("/api/me", headers=ana.headers).json()["name"] == "Ana"
    assert client.get("/api/me", headers=bruno.headers).json()["name"] == "Bruno"
    assert client.get("/api/me", headers={"Authorization": "Bearer nope"}).status_code == 401
