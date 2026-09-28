from fastapi import APIRouter, Depends

from app.deps import require_api_user
from app.models import User

router = APIRouter(prefix="/api", tags=["management"])


@router.get("/me")
def me(user: User = Depends(require_api_user)):
    """Quick check that the API token works."""
    return {"id": user.id, "name": user.name}