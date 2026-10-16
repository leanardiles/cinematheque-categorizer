"""Run a sync for every connected user from the terminal, without the per-run limit.

Run from backend/ with the venv active:
    op run --env-file=../.env.op -- python -m app.sync_run
"""

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.sync import run


def main() -> None:
    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(User.stremio_auth_key.is_not(None)).order_by(User.id)
        ).all()
        for user in users:
            report = run(db, user, limit=None)
            print(
                f"{user.name}: added {report.added}, linked {report.linked}, "
                f"removed {report.removed}."
            )


if __name__ == "__main__":
    main()