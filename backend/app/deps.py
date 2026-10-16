import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.accounts import WEB, user_for_token
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def tokens_match(given: str | None, expected: str) -> bool:
    # compare_digest takes the same time whether or not the tokens match,
    # so response timing cannot be used to guess the token
    return given is not None and secrets.compare_digest(given, expected)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_api_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """Protects the management API: Authorization: Bearer <the user's web token>."""
    user = user_for_token(db, WEB, credentials.credentials if credentials else None)
    if user is None:
        raise unauthorized()
    return user
