from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    CollectionCreate,
    CollectionOut,
    CollectionUpdate,
    OrderUpdate,
)
from app.db import get_db
from app.deps import require_api_user
from app.models import Collection, CollectionTitle, User

router = APIRouter(prefix="/collections", tags=["collections"])


def get_owned_collection(db: Session, user: User, collection_id: int) -> Collection:
    collection = db.get(Collection, collection_id)
    if collection is None or collection.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection


def title_count(db: Session, collection_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(CollectionTitle)
        .where(CollectionTitle.collection_id == collection_id)
    )


def to_out(collection: Collection, count: int) -> CollectionOut:
    return CollectionOut(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        position=collection.position,
        title_count=count,
    )


def commit_or_conflict(db: Session) -> None:
    """Commit, turning a duplicate collection name into a clear 409 error."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A collection with this name already exists",
        )


@router.get("", response_model=list[CollectionOut])
def list_collections(user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    counts = dict(
        db.execute(
            select(CollectionTitle.collection_id, func.count())
            .join(Collection, Collection.id == CollectionTitle.collection_id)
            .where(Collection.user_id == user.id)
            .group_by(CollectionTitle.collection_id)
        ).all()
    )
    collections = db.scalars(
        select(Collection)
        .where(Collection.user_id == user.id)
        .order_by(Collection.position, Collection.name)
    ).all()
    return [to_out(c, counts.get(c.id, 0)) for c in collections]


@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(
    body: CollectionCreate,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    last_position = db.scalar(
        select(func.max(Collection.position)).where(Collection.user_id == user.id)
    )
    collection = Collection(
        user_id=user.id,
        name=body.name.strip(),
        description=body.description,
        position=(last_position or 0) + 1 if last_position is not None else 0,
    )
    db.add(collection)
    commit_or_conflict(db)
    return to_out(collection, 0)


@router.put("/order", response_model=list[CollectionOut])
def reorder_collections(
    body: OrderUpdate,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    collections = db.scalars(select(Collection).where(Collection.user_id == user.id)).all()
    by_id = {c.id: c for c in collections}
    if sorted(body.ids) != sorted(by_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids must list every collection exactly once",
        )
    for position, collection_id in enumerate(body.ids):
        by_id[collection_id].position = position
    db.commit()
    return list_collections(user=user, db=db)


@router.patch("/{collection_id}", response_model=CollectionOut)
def update_collection(
    collection_id: int,
    body: CollectionUpdate,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    collection = get_owned_collection(db, user, collection_id)
    # Only change the fields the request actually sent, so a missing
    # description isn't confused with clearing it
    if "name" in body.model_fields_set and body.name is not None:
        collection.name = body.name.strip()
    if "description" in body.model_fields_set:
        collection.description = body.description
    commit_or_conflict(db)
    return to_out(collection, title_count(db, collection.id))


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: int,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    collection = get_owned_collection(db, user, collection_id)
    db.delete(collection)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)