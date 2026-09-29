"""Show what a sync would change, without changing anything.

Run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.sync_preview
"""

from sqlalchemy import select

from app import stremio
from app.db import SessionLocal
from app.models import User
from app.sync import plan

SHOW = 10  # names listed per group


def main() -> None:
    entries = stremio.fetch_library()
    print(f"Stremio library: {len(entries)} films and series")

    with SessionLocal() as db:
        user = db.scalar(select(User).order_by(User.id).limit(1))
        result = plan(db, user, entries)

    print(f"\nWould add {len(result.new)}:")
    for entry in result.new[:SHOW]:
        print(f"  {entry.imdb_id}  {entry.name}")
    if len(result.new) > SHOW:
        print(f"  ... and {len(result.new) - SHOW} more")

    print(f"\nWould link {len(result.link)} (already in the database, now also from Stremio):")
    for title, _ in result.link[:SHOW]:
        print(f"  {title.imdb_id}  {title.name}")

    print(f"\nWould remove {len(result.remove)} (no longer in the Stremio library):")
    for title in result.remove[:SHOW]:
        print(f"  {title.imdb_id}  {title.name}")


if __name__ == "__main__":
    main()