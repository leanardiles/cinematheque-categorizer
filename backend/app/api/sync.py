import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts import WEB, user_for_token
from app.config import settings
from app.db import get_db
from app.deps import bearer, tokens_match, unauthorized
from app.models import User
from app.stremio import StremioError
from app.sync import NotConnected, run

router = APIRouter(tags=["sync"])

PER_RUN = 50  # new films per user per run; the rest wait for the next run


def sync_targets(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> list[User]:
    """SYNC_SECRET (the scheduled job) syncs every connected user; a user's web
    token (a Sync now button) syncs just that user."""
    token = credentials.credentials if credentials else None
    if tokens_match(token, settings.sync_secret):
        return list(
            db.scalars(
                select(User).where(User.stremio_auth_key.is_not(None)).order_by(User.id)
            )
        )
    user = user_for_token(db, WEB, token)
    if user is None:
        raise unauthorized()
    return [user]


def sync_user(db: Session, user: User) -> dict:
    try:
        return {"user": user.id, **run(db, user, limit=PER_RUN).as_dict()}
    except NotConnected:
        return {"user": user.id, "error": "Stremio account not connected"}
    except StremioError as err:
        return {"user": user.id, "error": f"Stremio: {err}"}
    except httpx.HTTPError:
        return {"user": user.id, "error": "Could not reach Stremio"}


@router.post("/sync")
def sync_library(users: list[User] = Depends(sync_targets), db: Session = Depends(get_db)):
    """Sync Stremio libraries: add new films, remove deleted ones.

    One user's failure (an expired auth key, say) doesn't stop the others,
    but the response is then a 502, so the scheduled job reports it.
    """
    results = [sync_user(db, user) for user in users]
    failed = any("error" in result for result in results)
    if failed and len(users) == 1:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=results[0]["error"])
    return JSONResponse({"users": results}, status_code=502 if failed else 200)
