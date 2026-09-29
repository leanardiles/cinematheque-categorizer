"""Client for Stremio's user API (unofficial; see docs/reference/stremio-library-api.md)."""

from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import settings

API_URL = "https://api.strem.io/api"
TIMEOUT = httpx.Timeout(30.0)
TYPES = ("movie", "series")


class StremioError(Exception):
    """Stremio returned an error, for example an expired auth key."""


@dataclass
class LibraryEntry:
    imdb_id: str
    type: str  # "movie" or "series"
    name: str
    poster: str | None
    added: datetime | None  # when it was saved to the Stremio library
    modified: datetime | None


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_library() -> list[LibraryEntry]:
    """Films and series saved in the Stremio library (not removed, IMDb IDs only)."""
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(
            f"{API_URL}/datastoreGet",
            json={
                "authKey": settings.stremio_auth_key,
                "collection": "libraryItem",
                "ids": [],
                "all": True,
            },
        )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise StremioError(data["error"].get("message", "Unknown Stremio error"))

    entries: dict[str, LibraryEntry] = {}
    for item in data.get("result", []):
        imdb_id = str(item.get("_id", ""))
        if item.get("removed") or item.get("type") not in TYPES or not imdb_id.startswith("tt"):
            continue
        entries[imdb_id] = LibraryEntry(
            imdb_id=imdb_id,
            type=item["type"],
            name=item.get("name") or imdb_id,
            poster=item.get("poster") or None,
            added=_parse_time(item.get("_ctime")),
            modified=_parse_time(item.get("_mtime")),
        )
    return list(entries.values())