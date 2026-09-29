from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app import cinemeta, tmdb
from app.api.schemas import SearchResult, TitleCreate, TitleOut, TitleUpdate
from app.db import get_db
from app.deps import require_api_user
from app.models import Collection, CollectionTitle, Title, TitleSource, User

router = APIRouter(tags=["library"])


def metahub_poster(imdb_id: str) -> str:
    return f"https://images.metahub.space/poster/medium/{imdb_id}/img"


def collection_ids_for(db: Session, title_ids: list[int]) -> dict[int, list[int]]:
    """Map each title ID to the IDs of the collections it's in."""
    result: dict[int, list[int]] = {title_id: [] for title_id in title_ids}
    if not title_ids:
        return result
    rows = db.execute(
        select(CollectionTitle.title_id, CollectionTitle.collection_id).where(
            CollectionTitle.title_id.in_(title_ids)
        )
    ).all()
    for title_id, collection_id in rows:
        result[title_id].append(collection_id)
    return result


def sources_for(db: Session, title_ids: list[int]) -> dict[int, list[str]]:
    """Map each title ID to the sources it's currently present in."""
    result: dict[int, list[str]] = {title_id: [] for title_id in title_ids}
    if not title_ids:
        return result
    rows = db.execute(
        select(TitleSource.title_id, TitleSource.source).where(
            TitleSource.title_id.in_(title_ids), TitleSource.present.is_(True)
        )
    ).all()
    for title_id, source in rows:
        result[title_id].append(source)
    return result


def to_out(title: Title, collection_ids: list[int], sources: list[str]) -> TitleOut:
    return TitleOut(
        id=title.id,
        imdb_id=title.imdb_id,
        type=title.type,
        name=title.name,
        original_title=title.original_title,
        english_name=title.english_name,
        original_language=title.original_language,
        year=title.year,
        poster=title.poster,
        collection_ids=sorted(collection_ids),
        sources=sorted(sources),
        added_at=title.added_at or title.created_at,
    )


def titles_out(db: Session, titles: list[Title]) -> list[TitleOut]:
    ids = [t.id for t in titles]
    collections = collection_ids_for(db, ids)
    sources = sources_for(db, ids)
    return [to_out(t, collections[t.id], sources[t.id]) for t in titles]


def get_owned_title(db: Session, user: User, title_id: int) -> Title:
    title = db.get(Title, title_id)
    if title is None or title.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    return title


def add_to_collection(db: Session, collection: Collection, title: Title) -> None:
    """Append a title to the end of a collection; does nothing if it's already there."""
    already = db.get(CollectionTitle, (collection.id, title.id))
    if already is not None:
        return
    last = db.scalar(
        select(CollectionTitle.position)
        .where(CollectionTitle.collection_id == collection.id)
        .order_by(CollectionTitle.position.desc())
        .limit(1)
    )
    db.add(
        CollectionTitle(
            collection_id=collection.id,
            title_id=title.id,
            position=0 if last is None else last + 1,
        )
    )


def fetch_metadata(body: TitleCreate) -> tmdb.TmdbTitle | cinemeta.CinemetaTitle:
    """Find the title on TMDB, falling back to Cinemeta for IMDb IDs TMDB doesn't know."""
    if body.imdb_id:
        found = tmdb.lookup(body.imdb_id) or cinemeta.lookup(body.imdb_id)
    else:
        found = tmdb.resolve(body.tmdb_id, body.type)
    if found is None or not found.imdb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Title not found, or it has no IMDb ID (needed for Stremio)",
        )
    return found


@router.get("/titles", response_model=list[TitleOut])
def list_titles(
    q: str | None = None,
    unsorted: bool = False,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    query = select(Title).where(Title.user_id == user.id)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                Title.name.ilike(pattern),
                Title.original_title.ilike(pattern),
                Title.english_name.ilike(pattern),
            )
        )
    if unsorted:
        query = query.where(
            ~exists().where(CollectionTitle.title_id == Title.id)
        )
    titles = db.scalars(query.order_by(Title.name)).all()
    return titles_out(db, titles)


@router.post("/titles", response_model=TitleOut, status_code=status.HTTP_201_CREATED)
def add_title(
    body: TitleCreate,
    response: Response,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    # Check the collections first, so a bad ID doesn't leave a half-done add
    collections = []
    for collection_id in body.collection_ids:
        collection = db.get(Collection, collection_id)
        if collection is None or collection.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found",
            )
        collections.append(collection)

    # If the title is already in the library, reuse it (no duplicates)
    title = None
    if body.imdb_id:
        title = db.scalar(
            select(Title).where(Title.user_id == user.id, Title.imdb_id == body.imdb_id)
        )
    elif body.tmdb_id:
        title = db.scalar(
            select(Title).where(
                Title.user_id == user.id,
                Title.tmdb_id == body.tmdb_id,
                Title.type == body.type,
            )
        )

    if title is None:
        found = fetch_metadata(body)
        title = db.scalar(
            select(Title).where(Title.user_id == user.id, Title.imdb_id == found.imdb_id)
        )

    if title is None:
        is_tmdb = isinstance(found, tmdb.TmdbTitle)
        title = Title(
            user_id=user.id,
            imdb_id=found.imdb_id,
            type=found.type,
            name=found.display_name if is_tmdb else found.name,
            original_title=found.original_title if is_tmdb else None,
            english_name=found.english_name if is_tmdb else found.name,
            original_language=found.original_language if is_tmdb else None,
            tmdb_id=found.tmdb_id if is_tmdb else None,
            year=found.year,
            poster=found.poster or metahub_poster(found.imdb_id),
            added_at=datetime.now(timezone.utc),
        )
        title.sources.append(TitleSource(source="manual"))
        db.add(title)
        db.flush()
    else:
        response.status_code = status.HTTP_200_OK  # already existed

    for collection in collections:
        add_to_collection(db, collection, title)
    db.commit()
    return titles_out(db, [title])[0]


@router.patch("/titles/{title_id}", response_model=TitleOut)
def update_title(
    title_id: int,
    body: TitleUpdate,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    title = get_owned_title(db, user, title_id)
    title.name = body.name.strip()
    db.commit()
    return titles_out(db, [title])[0]


@router.delete("/titles/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_title(
    title_id: int,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    title = get_owned_title(db, user, title_id)
    db.delete(title)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/search", response_model=list[SearchResult])
def search_titles(
    q: str = Query(min_length=1),
    type: Literal["movie", "series"] = "movie",
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    results = tmdb.search(q, type)
    tmdb_ids = [r.tmdb_id for r in results]
    in_library = dict(
        db.execute(
            select(Title.tmdb_id, Title.id).where(
                Title.user_id == user.id,
                Title.type == type,
                Title.tmdb_id.in_(tmdb_ids),
            )
        ).all()
    ) if tmdb_ids else {}
    return [
        SearchResult(
            tmdb_id=r.tmdb_id,
            type=r.type,
            name=r.display_name,
            original_title=r.original_title,
            english_name=r.english_name,
            original_language=r.original_language,
            year=r.year,
            poster=r.poster,
            in_library=r.tmdb_id in in_library,
            title_id=in_library.get(r.tmdb_id),
        )
        for r in results
    ]