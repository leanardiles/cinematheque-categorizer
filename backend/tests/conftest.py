"""Test setup: an in-memory SQLite database and two users, Ana and Bruno.

Run from backend/ with the venv active (no secrets needed):
    pip install -r requirements-dev.txt
    pytest
"""

import os

from cryptography.fernet import Fernet

# Settings are read when the app is imported, so fake values go in first
os.environ.update(
    DATABASE_URL="postgresql://test:test@localhost/test",  # never connected to
    TMDB_READ_TOKEN="test",
    SYNC_SECRET="sync-secret-for-tests-0123456789",
    ENCRYPTION_KEY=Fernet.generate_key().decode(),
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.accounts import ADDON, WEB, add_token, set_stremio_key  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Collection, CollectionTitle, Title, User  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override
    with Session() as session:
        yield session
    app.dependency_overrides.clear()


@pytest.fixture()
def client(db):
    return TestClient(app)


class Account:
    """A user with a film in one collection, plus their tokens."""

    def __init__(self, db, name: str, imdb_id: str, collection_name: str):
        self.user = User(name=name)
        db.add(self.user)
        db.flush()
        self.web = add_token(db, self.user, WEB)
        self.addon = add_token(db, self.user, ADDON)
        set_stremio_key(self.user, f"stremio-key-of-{name}")
        self.title = Title(user_id=self.user.id, imdb_id=imdb_id, type="movie", name=f"{name}'s film")
        self.collection = Collection(user_id=self.user.id, name=collection_name)
        db.add_all([self.title, self.collection])
        db.flush()
        db.add(CollectionTitle(collection_id=self.collection.id, title_id=self.title.id))
        db.commit()

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.web}"}


@pytest.fixture()
def ana(db):
    return Account(db, "Ana", "tt0000001", "French")


@pytest.fixture()
def bruno(db):
    return Account(db, "Bruno", "tt0000002", "Horror")
