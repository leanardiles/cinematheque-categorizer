"""Sync the Stremio library into the database.

Stremio is the source of truth for synced films:
  new       saved in Stremio, not in the database yet     -> add
  link      already in the database (added manually)      -> mark as also from Stremio
  remove    synced before, no longer saved in Stremio     -> delete, with its collection entries
Films added manually and never saved in Stremio are left alone.
"""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Title, TitleSource, User
from app.stremio import LibraryEntry

SOURCE = "stremio"


@dataclass
class SyncPlan:
    new: list[LibraryEntry] = field(default_factory=list)
    link: list[tuple[Title, LibraryEntry]] = field(default_factory=list)
    remove: list[Title] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.new or self.link or self.remove)


def plan(db: Session, user: User, entries: list[LibraryEntry]) -> SyncPlan:
    """Compare the Stremio library with the database, without changing anything."""
    titles = db.scalars(select(Title).where(Title.user_id == user.id)).all()
    by_imdb = {t.imdb_id: t for t in titles}

    synced_ids = set(
        db.scalars(
            select(TitleSource.title_id)
            .join(Title, Title.id == TitleSource.title_id)
            .where(Title.user_id == user.id, TitleSource.source == SOURCE)
        ).all()
    )
    in_stremio = {e.imdb_id for e in entries}

    result = SyncPlan()
    for entry in entries:
        title = by_imdb.get(entry.imdb_id)
        if title is None:
            result.new.append(entry)
        elif title.id not in synced_ids:
            result.link.append((title, entry))

    result.remove = [t for t in titles if t.id in synced_ids and t.imdb_id not in in_stremio]
    return result