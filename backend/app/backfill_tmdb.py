"""Fill TMDB fields for titles that don't have them yet.

Run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.backfill_tmdb
"""

from sqlalchemy import select

from app import tmdb
from app.db import SessionLocal
from app.models import Title


def main() -> None:
    with SessionLocal() as db:
        titles = db.scalars(select(Title).where(Title.tmdb_id.is_(None))).all()
        for title in titles:
            found = tmdb.lookup(title.imdb_id)
            if found is None:
                print(f"  not found on TMDB: {title.imdb_id} {title.name}")
                continue
            title.tmdb_id = found.tmdb_id
            title.original_title = found.original_title
            title.english_name = found.english_name
            title.original_language = found.original_language
            title.name = found.display_name
            title.year = found.year or title.year
            title.poster = found.poster or title.poster
            print(f"  {title.imdb_id}: {title.name} ({title.year}, {title.original_language})")
        db.commit()
        print(f"Updated {len(titles)} titles.")


if __name__ == "__main__":
    main()