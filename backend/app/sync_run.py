"""Run a sync from the terminal, without the per-run limit.

Run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.sync_run
"""

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.sync import run


def main() -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).order_by(User.id).limit(1))
        report = run(db, user, limit=None)
    print(f"Added {report.added}, linked {report.linked}, removed {report.removed}.")


if __name__ == "__main__":
    main()