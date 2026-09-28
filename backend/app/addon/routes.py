from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import current_user, tokens_match
from app.models import Collection, CollectionTitle, Title

router = APIRouter()

PAGE_SIZE = 100  # Stremio's page size; fewer results means end of catalog
CACHE_SECONDS = 10
CATALOG_PREFIX = "collection-"


def check_token(token: str) -> None:
    if not tokens_match(token, settings.addon_token):
        raise HTTPException(status_code=404)


def cached(content: dict) -> JSONResponse:
    return JSONResponse(
        content, headers={"Cache-Control": f"max-age={CACHE_SECONDS}"}
    )


def collection_types(db: Session, collection: Collection) -> list[str]:
    """Content types present in a collection; Stremio catalogs have one type each."""
    types = db.scalars(
        select(Title.type)
        .join(CollectionTitle, CollectionTitle.title_id == Title.id)
        .where(CollectionTitle.collection_id == collection.id)
        .distinct()
    ).all()
    return sorted(types) or ["movie"]


@router.get("/{token}/manifest.json")
def manifest(token: str, db: Session = Depends(get_db)):
    check_token(token)
    user = current_user(db)

    collections = db.scalars(
        select(Collection)
        .where(Collection.user_id == user.id)
        .order_by(Collection.position, Collection.name)
    ).all()

    catalogs = []
    for collection in collections:
        for type_ in collection_types(db, collection):
            catalogs.append(
                {
                    "type": type_,
                    "id": f"{CATALOG_PREFIX}{collection.id}",
                    "name": f"{collection.name} Cinematheque",
                    "extra": [{"name": "skip", "isRequired": False}],
                }
            )

    return cached(
        {
            "id": "com.leanardiles.cinematheque",
            "version": "0.2.0",
            "name": "Cinematheque",
            "description": "My library, organized into collections.",
            "resources": ["catalog"],
            "types": ["movie", "series"],
            "idPrefixes": ["tt"],
            "catalogs": catalogs,
        }
    )


def parse_extra(extra: str | None) -> dict[str, str]:
    """Turn 'skip=100&genre=French' into {'skip': '100', 'genre': 'French'}."""
    if not extra:
        return {}
    return {key: values[0] for key, values in parse_qs(extra).items()}


def catalog_response(
    token: str, type: str, catalog_id: str, extra: str | None, db: Session
) -> JSONResponse:
    check_token(token)
    user = current_user(db)

    if not catalog_id.startswith(CATALOG_PREFIX):
        return cached({"metas": []})
    try:
        collection_id = int(catalog_id[len(CATALOG_PREFIX):])
        skip = int(parse_extra(extra).get("skip", 0))
    except ValueError:
        return cached({"metas": []})

    titles = db.scalars(
        select(Title)
        .join(CollectionTitle, CollectionTitle.title_id == Title.id)
        .join(Collection, Collection.id == CollectionTitle.collection_id)
        .where(
            Collection.id == collection_id,
            Collection.user_id == user.id,
            Title.type == type,
        )
        .order_by(CollectionTitle.position, CollectionTitle.added_at)
        .offset(skip)
        .limit(PAGE_SIZE)
    ).all()

    metas = [
        {
            "id": title.imdb_id,
            "type": title.type,
            "name": title.name,
            "poster": title.poster,
            "releaseInfo": str(title.year) if title.year else None,
        }
        for title in titles
    ]
    return cached({"metas": metas})


@router.get("/{token}/catalog/{type}/{catalog_id}.json")
def catalog(token: str, type: str, catalog_id: str, db: Session = Depends(get_db)):
    return catalog_response(token, type, catalog_id, None, db)


@router.get("/{token}/catalog/{type}/{catalog_id}/{extra}.json")
def catalog_with_extra(
    token: str, type: str, catalog_id: str, extra: str, db: Session = Depends(get_db)
):
    return catalog_response(token, type, catalog_id, extra, db)