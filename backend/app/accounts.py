"""User accounts: tokens and the encrypted Stremio auth key.

Tokens are random strings handed to the user once (in an addon address or
for the web app). The database keeps only their SHA-256 hash: tokens are
long and random, so a plain hash is enough, no slow password hashing needed.

Commands, run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.accounts list
    op run --env-file=../.env.op -- python -m app.accounts invite "Name"
    op run --env-file=../.env.op -- python -m app.accounts new-link <user id>
    op run --env-file=../.env.op -- python -m app.accounts revoke <user id>
    op run --env-file=../.env.op -- python -m app.accounts import-env
"""

import hashlib
import secrets
import sys
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, UserToken

WEB = "web"  # signs in to the web app and the management API
ADDON = "addon"  # the private part of the Stremio addon address
KINDS = (WEB, ADDON)

# Labels with a meaning. Invite links stop working once the user has created a
# password login; login tokens are the sessions that signing out revokes.
INVITE = "Invite link"
LOGIN = "Login"

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


def token_for(db: Session, kind: str, token: str | None) -> UserToken | None:
    """The stored token, or None if it's unknown or revoked."""
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
    return row


def user_for_token(db: Session, kind: str, token: str | None) -> User | None:
    """The user a token belongs to, or None if it's unknown or revoked."""
    row = token_for(db, kind, token)
    return row.user if row else None


def revoke_tokens(user: User, label: str) -> None:
    now = datetime.now(timezone.utc)
    for row in user.tokens:
        if row.label == label and row.revoked_at is None:
            row.revoked_at = now


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------

# Argon2id with the library's defaults: slow and salted on purpose, unlike
# token hashes, because people choose guessable passwords
_hasher = PasswordHasher()
# Compared against when the email is unknown, so a wrong email takes as long
# as a wrong password and response times don't reveal which emails exist
_DUMMY_HASH = _hasher.hash("not a real password")

MIN_PASSWORD = 8
MAX_FAILURES = 5  # wrong passwords in a row before a pause
LOCK_TIME = timedelta(minutes=15)


def set_password(user: User, password: str) -> None:
    user.password_hash = _hasher.hash(password)
    user.login_failures = 0
    user.login_locked_until = None


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:  # SQLite (tests) drops time zones
        return value.replace(tzinfo=timezone.utc)
    return value


def is_locked(user: User) -> bool:
    locked = _aware(user.login_locked_until)
    return locked is not None and locked > datetime.now(timezone.utc)


def check_password(user: User | None, password: str) -> bool:
    """True if the password is right. Counts failures towards the pause."""
    stored = user.password_hash if user and user.password_hash else _DUMMY_HASH
    try:
        ok = _hasher.verify(stored, password) and user is not None and bool(user.password_hash)
    except (VerificationError, InvalidHashError):
        ok = False
    if user is None:
        return False
    if ok:
        user.login_failures = 0
        user.login_locked_until = None
        if _hasher.check_needs_rehash(user.password_hash):
            user.password_hash = _hasher.hash(password)
    else:
        user.login_failures = (user.login_failures or 0) + 1
        if user.login_failures >= MAX_FAILURES:
            user.login_locked_until = datetime.now(timezone.utc) + LOCK_TIME
            user.login_failures = 0
    return ok


def normalize_email(email: str) -> str:
    return email.strip().lower()


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


def invite_link(token: str) -> str:
    # After the #, the token stays in the browser: it's never sent to a server
    # or written to request logs, and the web app removes it from the address bar
    return f"{settings.ui_url.rstrip('/')}/#invite={token}"


def _user_arg(db: Session, args: list[str]) -> User:
    if not args or not args[0].isdigit():
        sys.exit("Give the user's ID (see: python -m app.accounts list).")
    user = db.get(User, int(args[0]))
    if user is None:
        sys.exit(f"No user with ID {args[0]}.")
    return user


def _first_user(db: Session) -> User:
    user = db.scalar(select(User).order_by(User.id).limit(1))
    if user is None:
        sys.exit("No users in the database.")
    return user


def cmd_invite(db: Session, args: list[str]) -> None:
    """Create a user and print their invite link."""
    name = " ".join(args).strip()
    if not name:
        sys.exit('Give a name: python -m app.accounts invite "Name"')
    user = User(name=name[:100])
    db.add(user)
    db.flush()
    token = add_token(db, user, WEB, INVITE)
    db.commit()
    print(f"Created user {user.id} ({user.name}). Send them this link:\n")
    print(f"  {invite_link(token)}\n")
    print("It asks them to create an email and password login, then walks them")
    print("through connecting Stremio and installing their addon. The link stops")
    print("working once their login exists. It's shown only once.")


def cmd_new_link(db: Session, args: list[str]) -> None:
    """A fresh invite link for an existing user, for example after a forgotten password.

    The link lets them choose a new password (no current password needed).
    """
    user = _user_arg(db, args)
    token = add_token(db, user, WEB, INVITE)
    db.commit()
    print(f"New link for {user.name}. It lets them choose a new password:\n")
    print(f"  {invite_link(token)}")


def cmd_revoke(db: Session, args: list[str]) -> None:
    """Revoke every token of a user: web app links and addon addresses."""
    user = _user_arg(db, args)
    now = datetime.now(timezone.utc)
    count = 0
    for token in user.tokens:
        if token.revoked_at is None:
            token.revoked_at = now
            count += 1
    db.commit()
    print(f"Revoked {count} tokens for {user.name}. Create new ones with new-link.")


def cmd_list(db: Session, args: list[str]) -> None:
    for user in db.scalars(select(User).order_by(User.id)):
        active = [t for t in user.tokens if t.revoked_at is None]
        counts = {kind: sum(t.kind == kind for t in active) for kind in KINDS}
        kinds = ", ".join(f"{n} {kind}" for kind, n in counts.items() if n) or "no tokens"
        stremio = "Stremio connected" if user.stremio_auth_key else "Stremio not connected"
        login = user.email if user.password_hash else "no login yet"
        print(f"{user.id:>3}  {user.name:<20} {login:<30} {kinds:<20} {stremio}")


def cmd_import_env(db: Session, args: list[str]) -> None:
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


COMMANDS = {
    "list": cmd_list,
    "invite": cmd_invite,
    "new-link": cmd_new_link,
    "revoke": cmd_revoke,
    "import-env": cmd_import_env,
}


def main() -> None:
    from app.db import SessionLocal

    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"Usage: python -m app.accounts [{' | '.join(COMMANDS)}]")
    with SessionLocal() as db:
        COMMANDS[sys.argv[1]](db, sys.argv[2:])


if __name__ == "__main__":
    main()
