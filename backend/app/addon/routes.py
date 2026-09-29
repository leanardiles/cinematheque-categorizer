from urllib.parse import parse_qs, quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import current_user, tokens_match
from app.models import Collection, CollectionTitle, Title

router = APIRouter()

PAGE_SIZE = 100  # Stremio's page size; fewer results means end of catalog
CACHE_SECONDS = 10
CATALOG_PREFIX = "collection-"
ALL_CATALOG = "cinematheque-all"
# EXPERIMENT (branch experiment/stremio-deep-links): search-only catalog that
# receives stremio:///search deep links; hidden from Board because search is required
ACTIONS_CATALOG = "cinematheque-actions"
UNSORTED_CATALOG = "cinematheque-unsorted"


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


def library_types(db: Session, user_id: int) -> list[str]:
    """Content types present in the whole library."""
    types = db.scalars(select(Title.type).where(Title.user_id == user_id).distinct()).all()
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

    # All and Unsorted first, then the collections in their sidebar order
    catalogs = []
    special = ((ALL_CATALOG, "Cinematheque All"), (UNSORTED_CATALOG, "Cinematheque Unsorted"))
    for catalog_id, name in special:
        for type_ in library_types(db, user.id):
            catalogs.append(
                {
                    "type": type_,
                    "id": catalog_id,
                    "name": name,
                    "extra": [{"name": "skip", "isRequired": False}],
                }
            )
    for collection in collections:
        for type_ in collection_types(db, collection):
            catalogs.append(
                {
                    "type": type_,
                    "id": f"{CATALOG_PREFIX}{collection.id}",
                    "name": f"{collection.name} Cinematheque",
                    "extra": [
                        {"name": "skip", "isRequired": False},
                        # EXPERIMENT: lets a discover deep link pass a value in
                        {"name": "genre", "isRequired": False, "options": ["All"]},
                    ],
                }
            )

    # EXPERIMENT: search-only catalog for the search deep link test
    catalogs.append(
        {
            "type": "movie",
            "id": ACTIONS_CATALOG,
            "name": "Cinémathèque",
            "extra": [{"name": "search", "isRequired": True}],
        }
    )

    return cached(
        {
            "id": "com.leanardiles.cinematheque",
            "version": "0.5.0",
            "name": "Cinematheque",
            "description": "My library, organized into collections.",
            "resources": [
                "catalog",
                # Collection actions appear as sources on each film's page
                {"name": "stream", "types": ["movie", "series"], "idPrefixes": ["tt"]},
            ],
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


def to_meta(title: Title) -> dict:
    """A Stremio meta preview for one title."""
    return {
        "id": title.imdb_id,
        "type": title.type,
        "name": title.name,
        "poster": title.poster,
        "releaseInfo": str(title.year) if title.year else None,
    }


def catalog_response(
    token: str, type: str, catalog_id: str, extra: str | None, db: Session
) -> JSONResponse:
    check_token(token)
    user = current_user(db)

    params = parse_extra(extra)
    try:
        skip = int(params.get("skip", 0))
    except ValueError:
        return cached({"metas": []})

    # EXPERIMENT: log deep link hits so we can see which ones reach the backend
    if catalog_id == ACTIONS_CATALOG or "genre" in params:
        print(f"DEEPLINK catalog={catalog_id} type={type} params={params}", flush=True)
    if catalog_id == ACTIONS_CATALOG:
        # Answer with the whole library so the search page shows something from us
        titles = db.scalars(
            select(Title)
            .where(Title.user_id == user.id, Title.type == type)
            .order_by(func.coalesce(Title.added_at, Title.created_at).desc())
            .limit(20)
        ).all()
        return not_cached({"metas": [to_meta(title) for title in titles]})

    if catalog_id in (ALL_CATALOG, UNSORTED_CATALOG):
        # Most recently saved first, like the web app's default
        query = select(Title).where(Title.user_id == user.id, Title.type == type)
        if catalog_id == UNSORTED_CATALOG:
            query = query.where(~exists().where(CollectionTitle.title_id == Title.id))
        titles = db.scalars(
            query.order_by(func.coalesce(Title.added_at, Title.created_at).desc(), Title.name)
            .offset(skip)
            .limit(PAGE_SIZE)
        ).all()
        return cached({"metas": [to_meta(title) for title in titles]})

    if not catalog_id.startswith(CATALOG_PREFIX):
        return cached({"metas": []})
    try:
        collection_id = int(catalog_id[len(CATALOG_PREFIX):])
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

    return cached({"metas": [to_meta(title) for title in titles]})


@router.get("/{token}/catalog/{type}/{catalog_id}.json")
def catalog(token: str, type: str, catalog_id: str, db: Session = Depends(get_db)):
    return catalog_response(token, type, catalog_id, None, db)


@router.get("/{token}/catalog/{type}/{catalog_id}/{extra}.json")
def catalog_with_extra(
    token: str, type: str, catalog_id: str, extra: str, db: Session = Depends(get_db)
):
    return catalog_response(token, type, catalog_id, extra, db)


# ---------------------------------------------------------------------------
# Collection actions from inside Stremio (Milestone 6)
#
# Stremio lets addons add sources to a film's page, not buttons. So each
# collection becomes a source: selecting it calls /act/..., which adds or
# removes the film and redirects to a short confirmation clip. Because it is
# ordinary playback, it works on every Stremio app, including TV.
# The addon token in the path is what authorizes the change, like the manifest.
# ---------------------------------------------------------------------------

STREAM_NAME = "Cinémathèque"
CLIPS = {"add": "added.mp4", "remove": "removed.mp4"}


def external_links(url: str) -> dict:
    """EXPERIMENT: TV apps ignore externalUrl and read their own field instead."""
    return {"externalUrl": url, "androidTvUrl": url, "tizenUrl": url, "webosUrl": url}


def public_base(request: Request) -> str:
    """The address Stremio used to reach us, e.g. https://cinematheque-api.vercel.app."""
    proto = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host.split(',')[0].strip()}"


def not_cached(content: dict) -> JSONResponse:
    # Source lists change as soon as a film is filed, so never reuse an old one
    return JSONResponse(content, headers={"Cache-Control": "no-cache"})


@router.get("/{token}/stream/{type}/{video_id}.json")
def streams(token: str, type: str, video_id: str, request: Request, db: Session = Depends(get_db)):
    check_token(token)
    user = current_user(db)

    # Series episodes arrive as tt1234567:1:2; collections hold the series itself
    imdb_id = video_id.split(":")[0]
    title = db.scalar(select(Title).where(Title.user_id == user.id, Title.imdb_id == imdb_id))
    if title is None:
        # Saved in Stremio moments ago? Bring it in now instead of waiting for
        # the scheduled sync (Stremio stays the source of truth: films that
        # aren't saved there still get no entries)
        from app.sync import sync_one

        title = sync_one(db, user, imdb_id)
    if title is None:
        return not_cached({"streams": []})  # not in the library: nothing to file

    in_collections = set(
        db.scalars(
            select(CollectionTitle.collection_id).where(CollectionTitle.title_id == title.id)
        ).all()
    )
    collections = db.scalars(
        select(Collection)
        .where(Collection.user_id == user.id)
        .order_by(Collection.position, Collection.name)
    ).all()

    base = public_base(request)
    result = []
    for collection in collections:
        if collection.id in in_collections:
            action, text = "remove", f"✓ In {collection.name}\nSelect to remove"
        else:
            action, text = "add", f"＋ Add to {collection.name}"
        result.append(
            {
                "name": STREAM_NAME,
                "description": text,
                "url": f"{base}/{token}/act/{action}/{collection.id}/{imdb_id}.mp4",
            }
        )

    # EXPERIMENT: three kinds of internal Stremio links, to see which ones the
    # apps follow and which reach the backend (look for DEEPLINK in the logs)
    manifest_url = f"{base}/{token}/manifest.json"
    first = collections[0] if collections else None
    if first is not None:
        marker = f"cinematheque add {first.id} {imdb_id}"
        result.append(
            {
                "name": "Test 1",
                "description": f"Search link ({first.name})",
                **external_links(f"stremio:///search?search={quote(marker)}"),
            }
        )
        result.append(
            {
                "name": "Test 2",
                "description": f"Discover link ({first.name})",
                **external_links(
                    f"stremio:///discover/{quote(manifest_url, safe='')}"
                    f"/{title.type}/{CATALOG_PREFIX}{first.id}?genre=All"
                ),
            }
        )
    result.append(
        {
            "name": "Test 3",
            "description": "Detail link (control)",
            **external_links(f"stremio:///detail/{title.type}/{imdb_id}/{imdb_id}"),
        }
    )

    # Opens the web app with this film searched (desktop and phone; TVs usually can't)
    result.append(
        {
            "name": STREAM_NAME,
            "description": "Open in the Cinémathèque app",
            **external_links(f"{settings.ui_url}/?q={quote(title.name)}"),
        }
    )
    return not_cached({"streams": result})


@router.api_route("/{token}/act/{action}/{collection_id}/{imdb_id}.mp4", methods=["GET", "HEAD"])
def act(
    token: str,
    action: str,
    collection_id: int,
    imdb_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Add or remove a film, then play the matching confirmation clip.

    Explicit add/remove (never toggle), so a player requesting the address
    more than once, as video players often do, can't undo the change.
    """
    from app.api.titles import add_to_collection  # shared with the web app's API

    check_token(token)
    if action not in CLIPS:
        raise HTTPException(status_code=404)
    user = current_user(db)

    collection = db.get(Collection, collection_id)
    title = db.scalar(select(Title).where(Title.user_id == user.id, Title.imdb_id == imdb_id))
    if collection is None or collection.user_id != user.id or title is None:
        raise HTTPException(status_code=404)

    entry = db.get(CollectionTitle, (collection.id, title.id))
    if action == "add" and entry is None:
        add_to_collection(db, collection, title)
        db.commit()
    elif action == "remove" and entry is not None:
        db.delete(entry)
        db.commit()

    return RedirectResponse(
        f"{public_base(request)}/clips/{CLIPS[action]}",
        status_code=302,
        headers={"Cache-Control": "no-store"},
    )
