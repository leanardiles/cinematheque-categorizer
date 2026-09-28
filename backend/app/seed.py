"""Seed the database with a user, collections and films.

Run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.seed

Safe to run repeatedly: existing rows are reused, missing ones are added.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Collection, CollectionTitle, Title, TitleSource, User

USER_NAME = "Leandro"


def poster_url(imdb_id: str) -> str:
    return f"https://images.metahub.space/poster/medium/{imdb_id}/img"


# Films in the library: (imdb_id, type, name, year)
FILMS = [
    ("tt0185125", "movie", "Todo sobre mi madre", 1999),
    ("tt0211915", "movie", "Amélie", 2001),
    ("tt0113247", "movie", "La haine", 1995),
    ("tt8613070", "movie", "Portrait de la jeune fille en feu", 2019),
    ("tt1305806", "movie", "El secreto de sus ojos", 2009),
    ("tt3011894", "movie", "Relatos salvajes", 2014),
    ("tt0247586", "movie", "Nueve reinas", 2000),
    ("tt4975722", "movie", "Moonlight", 2016),
    ("tt5726616", "movie", "Call Me by Your Name", 2017),
]

# Collections in display order, each with its films in display order
COLLECTIONS = [
    ("French", ["tt0211915", "tt0113247", "tt8613070"]),
    ("Argentinian", ["tt1305806", "tt3011894", "tt0247586"]),
    ("LGBTQ+", ["tt0185125", "tt8613070", "tt4975722", "tt5726616"]),
]


def get_or_create_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.name == USER_NAME))
    if user is None:
        user = User(name=USER_NAME)
        db.add(user)
        db.flush()  # assigns user.id
    return user


def upsert_titles(db: Session, user: User) -> dict[str, Title]:
    titles: dict[str, Title] = {}
    for imdb_id, type_, name, year in FILMS:
        title = db.scalar(
            select(Title).where(Title.user_id == user.id, Title.imdb_id == imdb_id)
        )
        if title is None:
            title = Title(
                user_id=user.id,
                imdb_id=imdb_id,
                type=type_,
                name=name,
                year=year,
                poster=poster_url(imdb_id),
            )
            title.sources.append(TitleSource(source="manual"))
            db.add(title)
        titles[imdb_id] = title
    db.flush()  # assigns title ids
    return titles


def upsert_collections(db: Session, user: User, titles: dict[str, Title]) -> None:
    for c_pos, (name, imdb_ids) in enumerate(COLLECTIONS):
        collection = db.scalar(
            select(Collection).where(
                Collection.user_id == user.id, Collection.name == name
            )
        )
        if collection is None:
            collection = Collection(user_id=user.id, name=name)
            db.add(collection)
        collection.position = c_pos
        db.flush()

        existing = {entry.title_id: entry for entry in collection.entries}
        for t_pos, imdb_id in enumerate(imdb_ids):
            title = titles[imdb_id]
            entry = existing.get(title.id)
            if entry is None:
                collection.entries.append(
                    CollectionTitle(title_id=title.id, position=t_pos)
                )
            else:
                entry.position = t_pos


def main() -> None:
    with SessionLocal() as db:
        user = get_or_create_user(db)
        titles = upsert_titles(db, user)
        upsert_collections(db, user, titles)
        db.commit()

        count = db.scalar(select(Title.id).where(Title.user_id == user.id).limit(1))
        print(f"Seeded user '{user.name}' (id {user.id}).")
        for collection in sorted(
            db.scalars(select(Collection).where(Collection.user_id == user.id)),
            key=lambda c: c.position,
        ):
            names = [entry.title.name for entry in collection.entries]
            print(f"  {collection.name}: {', '.join(names)}")


if __name__ == "__main__":
    main()