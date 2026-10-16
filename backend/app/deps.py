import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.accounts import WEB, token_for
from app.db import get_db
from app.models import User, UserToken

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


def require_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> UserToken:
    """The web token the request was made with (for sign-out and invite checks)."""
    row = token_for(db, WEB, credentials.credentials if credentials else None)
    if row is None:
        raise unauthorized()
    return row


def require_api_user(token: UserToken = Depends(require_api_token)) -> User:
    """Protects the management API: Authorization: Bearer <the user's web token>."""
    return token.user
