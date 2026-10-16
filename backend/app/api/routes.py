from fastapi import APIRouter, Depends

from app.api import collections, sync, titles
from app.deps import require_api_user
from app.models import User


router = APIRouter(prefix="/api", tags=["management"])
router.include_router(collections.router)
router.include_router(titles.router)
router.include_router(sync.router)


@router.get("/me")
def me(user: User = Depends(require_api_user)):
    """Who the token belongs to, and whether their Stremio account is connected."""
    return {"id": user.id, "name": user.name, "stremio_connected": user.stremio_auth_key is not None}