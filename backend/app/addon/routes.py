from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter()


def check_token(token: str) -> None:
    if token != settings.addon_token:
        raise HTTPException(status_code=404)


@router.get("/{token}/manifest.json")
def manifest(token: str):
    check_token(token)
    return {
        "id": "com.leanardiles.cinematheque",
        "version": "0.1.0",
        "name": "Cinematheque",
        "description": "My saved library, tagged and filterable.",
        "resources": ["catalog"],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"],
        "catalogs": [
            {
                "type": "movie",
                "id": "cinematheque-movies",
                "name": "Cinematheque: Movies",
            }
        ],
    }


@router.get("/{token}/catalog/{type}/{catalog_id}.json")
def catalog(token: str, type: str, catalog_id: str):
    check_token(token)
    # Hardcoded for now; replaced by database queries later
    return {
        "metas": [
            {
                "id": "tt0185125",
                "type": "movie",
                "name": "Todo sobre mi madre",
                "poster": "https://images.metahub.space/poster/medium/tt0185125/img",
            }
        ]
    }