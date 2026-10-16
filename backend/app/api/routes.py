from fastapi import APIRouter, Depends

from app.api import account, collections, sync, titles
from app.accounts import INVITE
from app.deps import require_api_token
from app.models import UserToken


router = APIRouter(prefix="/api", tags=["management"])
router.include_router(collections.router)
router.include_router(titles.router)
router.include_router(sync.router)
router.include_router(account.router)


@router.get("/me")
def me(token: UserToken = Depends(require_api_token)):
    """Who the token belongs to, their login and whether Stremio is connected."""
    user = token.user
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email if user.password_hash else None,
        "has_password": user.password_hash is not None,
        # Signed in with an invite link: the web app asks them to create a login
        "via_invite": token.label == INVITE,
        "stremio_connected": user.stremio_auth_key is not None,
    }