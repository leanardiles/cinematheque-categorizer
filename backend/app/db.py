from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings


def _sqlalchemy_url(url: str) -> str:
    # Supabase gives postgresql://; SQLAlchemy needs the driver name for psycopg 3
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


engine = create_engine(
    _sqlalchemy_url(settings.database_url),
    # The transaction pooler already pools connections, and serverless
    # functions are short-lived, so SQLAlchemy should not keep its own pool
    poolclass=NullPool,
    # The transaction pooler does not support prepared statements
    connect_args={"prepare_threshold": None},
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that provides a session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()