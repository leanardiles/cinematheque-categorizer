"""Show what a sync would change, without changing anything.

Run from backend/ with the venv active (optionally with a user ID; default
the first user):
    op run --env-file=../.env.op -- python -m app.sync_preview [user_id]
"""

import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.sync import fetch_library, plan

SHOW = 10  # names listed per group


def main() -> None:
    with SessionLocal() as db:
        if len(sys.argv) > 1:
            user = db.get(User, int(sys.argv[1]))
        else:
            user = db.scalar(select(User).order_by(User.id).limit(1))
        if user is None:
            sys.exit("User not found.")
        entries = fetch_library(user)
        print(f"{user.name}'s Stremio library: {len(entries)} films and series")
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