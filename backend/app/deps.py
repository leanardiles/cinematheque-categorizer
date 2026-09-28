import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def tokens_match(given: str | None, expected: str) -> bool:
    # compare_digest takes the same time whether or not the tokens match,
    # so response timing cannot be used to guess the token
    return given is not None and secrets.compare_digest(given, expected)


def current_user(db: Session) -> User:
    # Single user for now; with multi-user support the token will identify the user
    user = db.scalar(select(User).order_by(User.id).limit(1))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user


def require_api_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """Protects the management API: requires Authorization: Bearer <API_TOKEN>."""
    token = credentials.credentials if credentials else None
    if not tokens_match(token, settings.api_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user(db)