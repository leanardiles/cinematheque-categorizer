from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class CollectionOut(BaseModel):
    id: int
    name: str
    description: str | None
    position: int
    title_count: int


class OrderUpdate(BaseModel):
    ids: list[int]


class TitleOut(BaseModel):
    id: int
    imdb_id: str
    type: str
    name: str
    original_title: str | None
    english_name: str | None
    original_language: str | None
    year: int | None
    poster: str | None
    collection_ids: list[int]
    sources: list[str]
    added_at: datetime


class TitleCreate(BaseModel):
    """Add a title either by IMDb ID or by a TMDB search result."""

    imdb_id: str | None = Field(default=None, pattern=r"^tt\d+$")
    tmdb_id: int | None = None
    type: Literal["movie", "series"] | None = None
    collection_ids: list[int] = []

    @model_validator(mode="after")
    def check_identifier(self):
        if self.imdb_id is None and (self.tmdb_id is None or self.type is None):
            raise ValueError("Provide imdb_id, or tmdb_id together with type")
        return self


class TitleUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=300)


class SearchResult(BaseModel):
    tmdb_id: int
    type: str
    name: str
    original_title: str
    english_name: str | None
    original_language: str | None
    year: int | None
    poster: str | None
    in_library: bool
    title_id: int | None


class CollectionTitleAdd(BaseModel):
    title_id: int