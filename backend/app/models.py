from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Title(Base):
    """A film or series in a user's library, stored once per IMDb ID."""

    __tablename__ = "titles"
    __table_args__ = (UniqueConstraint("user_id", "imdb_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    imdb_id: Mapped[str] = mapped_column(String(20))
    type: Mapped[str] = mapped_column(String(10))  # "movie" or "series"
    name: Mapped[str] = mapped_column(String(300))  # display name shown in Stremio and the UI
    original_title: Mapped[str | None] = mapped_column(String(300))
    english_name: Mapped[str | None] = mapped_column(String(300))
    original_language: Mapped[str | None] = mapped_column(String(10))
    tmdb_id: Mapped[int | None] = mapped_column(Integer)
    year: Mapped[int | None] = mapped_column(Integer)
    poster: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sources: Mapped[list["TitleSource"]] = relationship(
        back_populates="title", cascade="all, delete-orphan"
    )


class TitleSource(Base):
    """Where a title came from: manual, stremio, letterboxd."""

    __tablename__ = "title_sources"
    __table_args__ = (UniqueConstraint("title_id", "source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(20))
    present: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    title: Mapped["Title"] = relationship(back_populates="sources")


class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = (UniqueConstraint("user_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    entries: Mapped[list["CollectionTitle"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="CollectionTitle.position",
    )


class CollectionTitle(Base):
    """A title placed in a collection, with its manual position."""

    __tablename__ = "collection_titles"

    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True
    )
    title_id: Mapped[int] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    collection: Mapped["Collection"] = relationship(back_populates="entries")
    title: Mapped["Title"] = relationship()