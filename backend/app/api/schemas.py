from pydantic import BaseModel, Field


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