"""The user's own account: email and password login, connecting Stremio, the addon address."""

import re
from datetime import datetime, timezone
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import stremio
from app.accounts import (
    ADDON,
    INVITE,
    LOGIN,
    MIN_PASSWORD,
    WEB,
    add_token,
    check_password,
    is_locked,
    normalize_email,
    revoke_tokens,
    set_password,
    set_stremio_key,
)
from app.db import get_db
from app.deps import require_api_token, require_api_user
from app.models import User, UserToken
from app.stremio import StremioError
from app.sync import run

router = APIRouter(tags=["account"])

FIRST_SYNC = 50  # films imported right away; the scheduled sync brings in the rest


class StremioConnect(BaseModel):
    # All optional, and the checks happen in code: FastAPI's own validation
    # errors echo the input back, which could include the password
    email: str | None = None
    password: str | None = None
    auth_key: str | None = None


def stremio_auth_key(body: StremioConnect) -> str:
    """Sign in with an email and password, or check a pasted auth key."""
    try:
        if body.auth_key and body.auth_key.strip():
            auth_key = body.auth_key.strip().strip('"')
            stremio.fetch_library(auth_key)  # proves the key works
            return auth_key
        if body.email and body.password:
            return stremio.login(body.email.strip(), body.password)
    except StremioError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Stremio didn't accept that access key."
                if body.auth_key
                else "Stremio didn't accept that email and password."
            ),
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach Stremio."
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Enter your Stremio email and password, or an access key.",
    )


@router.post("/stremio/connect")
def connect_stremio(
    body: StremioConnect, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    """Connect the user's Stremio account and import the first films."""
    set_stremio_key(user, stremio_auth_key(body))
    db.commit()
    try:
        report = run(db, user, limit=FIRST_SYNC).as_dict()
    except Exception:
        report = None  # connected anyway; the scheduled sync will import the library
    return {"connected": True, "sync": report}


@router.delete("/stremio/connect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_stremio(user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    """Forget the Stremio key. Films and collections stay; syncing stops."""
    set_stremio_key(user, None)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/addon-link")
def addon_link(
    request: Request, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    """A personal addon address, with install links for Stremio.

    Addon tokens are stored hashed, so an address can't be shown again later.
    Each call creates a fresh one instead; addresses installed earlier keep working.
    """
    from app.addon.routes import public_base

    token = add_token(db, user, ADDON, "Web app")
    db.commit()
    manifest_url = f"{public_base(request)}/{token}/manifest.json"
    host_and_path = manifest_url.split("://", 1)[1]
    return {
        "manifest_url": manifest_url,
        "app_install_url": f"stremio://{host_and_path}",
        "web_install_url": f"https://web.strem.io/#/addons?addon={quote(manifest_url, safe='')}",
    }


# ---------------------------------------------------------------------------
# Email and password login
# ---------------------------------------------------------------------------


class LoginBody(BaseModel):
    email: str | None = None
    password: str | None = None


class SetLoginBody(BaseModel):
    email: str | None = None
    password: str | None = None
    current_password: str | None = None


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WRONG_LOGIN = "Email or password is incorrect."


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    """Sign in with email and password; returns a web token for this device."""
    email = normalize_email(body.email or "")
    user = db.scalar(select(User).where(User.email == email)) if email else None
    if user is not None and is_locked(user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again in a few minutes.",
        )
    ok = check_password(user, body.password or "")
    db.commit()  # saves the failure count, or its reset
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=WRONG_LOGIN)
    token = add_token(db, user, WEB, LOGIN)
    db.commit()
    return {"token": token}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: UserToken = Depends(require_api_token), db: Session = Depends(get_db)):
    """Sign this device out. Only login sessions end here; invite links and the
    original token (which have no session to end) keep working."""
    if token.label == LOGIN:
        token.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/login")
def set_login(
    body: SetLoginBody,
    token: UserToken = Depends(require_api_token),
    db: Session = Depends(get_db),
):
    """Create or change the email and password login.

    Changing an existing password needs the current one, except when signed in
    with an invite link: that's how a forgotten password is reset (new-link).
    Afterwards invite links stop working and a fresh login token is returned.
    """
    user = token.user
    email = normalize_email(body.email or "")
    password = body.password or ""
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email.")
    if not MIN_PASSWORD <= len(password) <= 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Choose a password of at least {MIN_PASSWORD} characters.",
        )
    if user.password_hash and token.label != INVITE:
        if is_locked(user):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Try again in a few minutes.",
            )
        ok = check_password(user, body.current_password or "")
        db.commit()
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Your current password is incorrect."
            )
    taken = db.scalar(select(User).where(User.email == email, User.id != user.id))
    if taken is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This email is used by another account."
        )

    user.email = email
    set_password(user, password)
    revoke_tokens(user, INVITE)
    new_token = add_token(db, user, WEB, LOGIN)
    db.commit()
    return {"token": new_token, "email": email}
