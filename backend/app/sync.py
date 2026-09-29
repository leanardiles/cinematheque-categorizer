"""Sync the Stremio library into the database.

Stremio is the source of truth for synced films:
  new       saved in Stremio, not in the database yet     -> add
  link      already in the database (added manually)      -> mark as also from Stremio
  remove    synced before, no longer saved in Stremio     -> delete, with its collection entries
Films added manually and never saved in Stremio are left alone.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import stremio, tmdb
from app.models import Title, TitleSource, User
from app.stremio import LibraryEntry

SOURCE = "stremio"


@dataclass
class SyncPlan:
    new: list[LibraryEntry] = field(default_factory=list)
    link: list[tuple[Title, LibraryEntry]] = field(default_factory=list)
    remove: list[Title] = field(default_factory=list)
    # Already synced and still in Stremio; only used to fill in missing dates
    existing: list[tuple[Title, LibraryEntry]] = field(default_factory=list)

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
        else:
            result.existing.append((title, entry))

    result.remove = [t for t in titles if t.id in synced_ids and t.imdb_id not in in_stremio]
    return result

@dataclass
class SyncReport:
    added: int = 0
    linked: int = 0
    removed: int = 0
    remaining: int = 0  # new films left for the next run (limit reached)

    def as_dict(self) -> dict[str, int]:
        return {
            "added": self.added,
            "linked": self.linked,
            "removed": self.removed,
            "remaining": self.remaining,
        }


def _metahub_poster(imdb_id: str) -> str:
    return f"https://images.metahub.space/poster/medium/{imdb_id}/img"


def _new_title(user: User, entry: LibraryEntry) -> Title:
    """Build a Title from TMDB (original titles), falling back to what Stremio knows."""
    try:
        found = tmdb.lookup(entry.imdb_id)
    except Exception:
        found = None  # TMDB unreachable or slow; Stremio's data is good enough for now

    if found is not None:
        title = Title(
            user_id=user.id,
            imdb_id=entry.imdb_id,
            type=entry.type,
            name=found.display_name,
            original_title=found.original_title,
            english_name=found.english_name,
            original_language=found.original_language,
            tmdb_id=found.tmdb_id,
            year=found.year,
            poster=found.poster or entry.poster or _metahub_poster(entry.imdb_id),
            added_at=entry.added or datetime.now(timezone.utc),
        )
    else:
        title = Title(
            user_id=user.id,
            imdb_id=entry.imdb_id,
            type=entry.type,
            name=entry.name,
            english_name=entry.name,
            poster=entry.poster or _metahub_poster(entry.imdb_id),
            added_at=entry.added or datetime.now(timezone.utc),
        )
    title.sources.append(TitleSource(source=SOURCE))
    return title


def apply(db: Session, user: User, result: SyncPlan, limit: int | None = 50) -> SyncReport:
    """Apply a plan. Adds at most `limit` new films per run; the rest wait for the next run."""
    report = SyncReport()

    # Removed from Stremio: delete, including collection entries (cascade)
    for title in result.remove:
        db.delete(title)
        report.removed += 1

    # Already here from another source: mark as also coming from Stremio
    for title, entry in result.link:
        title.sources.append(TitleSource(source=SOURCE))
        if title.added_at is None:
            title.added_at = entry.added or title.created_at
        report.linked += 1

    # Films synced before dates were stored get Stremio's date once
    for title, entry in result.existing:
        if title.added_at is None and entry.added is not None:
            title.added_at = entry.added
    db.commit()

    # New films, committed one by one so a timeout never loses finished work
    batch = result.new if limit is None else result.new[:limit]
    for entry in batch:
        db.add(_new_title(user, entry))
        db.commit()
        report.added += 1
    report.remaining = len(result.new) - len(batch)

    # Everything still in Stremio was just seen
    db.execute(
        update(TitleSource)
        .where(TitleSource.source == SOURCE)
        .where(TitleSource.title_id.in_(select(Title.id).where(Title.user_id == user.id)))
        .values(last_seen=datetime.now(timezone.utc), present=True)
    )
    db.commit()
    return report


def run(db: Session, user: User, limit: int | None = 50) -> SyncReport:
    """Fetch the Stremio library, plan and apply. Used by the endpoint and the CLI."""
    entries = stremio.fetch_library()
    return apply(db, user, plan(db, user, entries), limit=limit)

def sync_one(db: Session, user: User, imdb_id: str) -> Title | None:
    """Bring in a single film right away, if it's saved in the Stremio library.

    Used when Stremio asks for a film's sources before the scheduled sync has
    picked it up. Returns the film, or None if it isn't in the Stremio library
    (or Stremio can't be reached; the scheduled sync will catch up).
    """
    try:
        entries = stremio.fetch_library()
    except Exception:
        return None
    entry = next((e for e in entries if e.imdb_id == imdb_id), None)
    if entry is None:
        return None

    title = _new_title(user, entry)
    db.add(title)
    try:
        db.commit()
    except IntegrityError:
        # Added by a sync running at the same moment; use that one
        db.rollback()
        title = db.scalar(
            select(Title).where(Title.user_id == user.id, Title.imdb_id == imdb_id)
        )
    return title
