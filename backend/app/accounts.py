"""User accounts: tokens and the encrypted Stremio auth key.

Tokens are random strings handed to the user once (in an addon address or
for the web app). The database keeps only their SHA-256 hash: tokens are
long and random, so a plain hash is enough, no slow password hashing needed.

Commands, run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.accounts list
    op run --env-file=../.env.op -- python -m app.accounts import-env
"""

import hashlib
import secrets
import sys
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, UserToken

WEB = "web"  # signs in to the web app and the management API
ADDON = "addon"  # the private part of the Stremio addon address
KINDS = (WEB, ADDON)

# last_used_at is a rough guide, so don't write to the database on every request
TOUCH_INTERVAL = timedelta(hours=1)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token() -> str:
    """43 URL-safe characters, 256 bits of randomness."""
    return secrets.token_urlsafe(32)


def add_token(db: Session, user: User, kind: str, label: str | None = None,
              token: str | None = None) -> str:
    """Store a token for the user and return it in plain text (shown only once)."""
    if kind not in KINDS:
        raise ValueError(f"Unknown token kind: {kind}")
    token = token or new_token()
    db.add(UserToken(user_id=user.id, kind=kind, token_hash=hash_token(token), label=label))
    return token


def user_for_token(db: Session, kind: str, token: str | None) -> User | None:
    """The user a token belongs to, or None if it's unknown or revoked."""
    if not token:
        return None
    row = db.scalar(
        select(UserToken).where(
            UserToken.token_hash == hash_token(token),
            UserToken.kind == kind,
            UserToken.revoked_at.is_(None),
        )
    )
    if row is None:
        return None
    now = datetime.now(timezone.utc)
    last = row.last_used_at
    if last is not None and last.tzinfo is None:  # SQLite (tests) drops time zones
        last = last.replace(tzinfo=timezone.utc)
    if last is None or now - last > TOUCH_INTERVAL:
        row.last_used_at = now
        db.commit()
    return row.user


def _fernet() -> Fernet:
    return Fernet(settings.encryption_key.encode())


def set_stremio_key(user: User, auth_key: str | None) -> None:
    user.stremio_auth_key = _fernet().encrypt(auth_key.encode()).decode() if auth_key else None


def stremio_key(user: User) -> str | None:
    """The user's Stremio auth key in plain text, or None if not connected."""
    if not user.stremio_auth_key:
        return None
    try:
        return _fernet().decrypt(user.stremio_auth_key.encode()).decode()
    except InvalidToken:
        return None  # encrypted with a different ENCRYPTION_KEY


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def _first_user(db: Session) -> User:
    user = db.scalar(select(User).order_by(User.id).limit(1))
    if user is None:
        sys.exit("No users in the database.")
    return user


def cmd_list(db: Session) -> None:
    for user in db.scalars(select(User).order_by(User.id)):
        active = [t for t in user.tokens if t.revoked_at is None]
        kinds = ", ".join(sorted(f"{t.kind}" for t in active)) or "no tokens"
        stremio = "Stremio connected" if user.stremio_auth_key else "Stremio not connected"
        print(f"{user.id:>3}  {user.name:<20} {kinds:<20} {stremio}")


def cmd_import_env(db: Session) -> None:
    """Move the old single-user ADDON_TOKEN, API_TOKEN and STREMIO_AUTH_KEY into the
    first user's account, so the installed addon and the web app keep working."""
    user = _first_user(db)
    pairs = [(ADDON, settings.addon_token, "Original addon address"),
             (WEB, settings.api_token, "Original web app token")]
    for kind, token, label in pairs:
        if not token:
            print(f"{kind}: no value in the environment, skipped")
            continue
        exists = db.scalar(select(UserToken).where(UserToken.token_hash == hash_token(token)))
        if exists:
            print(f"{kind}: already imported")
            continue
        add_token(db, user, kind, label, token=token)
        print(f"{kind}: imported")
    if settings.stremio_auth_key:
        set_stremio_key(user, settings.stremio_auth_key)
        print("Stremio auth key: imported (encrypted)")
    else:
        print("Stremio auth key: no value in the environment, skipped")
    db.commit()
    print(f"Done for user {user.id} ({user.name}).")


COMMANDS = {"list": cmd_list, "import-env": cmd_import_env}


def main() -> None:
    from app.db import SessionLocal

    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"Usage: python -m app.accounts [{' | '.join(COMMANDS)}]")
    with SessionLocal() as db:
        COMMANDS[sys.argv[1]](db)


if __name__ == "__main__":
    main()
