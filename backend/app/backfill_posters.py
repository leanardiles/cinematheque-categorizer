"""Replace posters with original-language ones where TMDB has them.

Run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.backfill_posters
"""

from sqlalchemy import select

from app import tmdb
from app.db import SessionLocal
from app.models import Title


def main() -> None:
    with SessionLocal() as db:
        titles = db.scalars(select(Title).where(Title.tmdb_id.is_not(None))).all()
        changed = 0
        for title in titles:
            if not title.original_title or not tmdb.is_latin(title.original_title):
                continue
            poster = tmdb.original_poster(title.tmdb_id, title.type, title.original_language)
            if poster and poster != title.poster:
                title.poster = poster
                changed += 1
                print(f"  {title.name}: new poster")
        db.commit()
        print(f"Updated {changed} of {len(titles)} titles.")


if __name__ == "__main__":
    main()