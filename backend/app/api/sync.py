import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import bearer, current_user, tokens_match
from app.models import User
from app.stremio import StremioError
from app.sync import run

router = APIRouter(tags=["sync"])


def require_sync_access(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """Accepts SYNC_SECRET (scheduled job) or API_TOKEN (a future Sync now button)."""
    token = credentials.credentials if credentials else None
    if not (tokens_match(token, settings.sync_secret) or tokens_match(token, settings.api_token)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user(db)


@router.post("/sync")
def sync_library(user: User = Depends(require_sync_access), db: Session = Depends(get_db)):
    """Sync the Stremio library: add new films (up to 50 per run), remove deleted ones."""
    try:
        report = run(db, user, limit=50)
    except StremioError as err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Stremio: {err}")
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach Stremio"
        )
    return report.as_dict()