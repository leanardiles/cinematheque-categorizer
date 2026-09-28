"""Minimal client for Cinemeta, Stremio's metadata service.

Used to look up and search films and series by IMDb ID or title, so the
library can store a name, year and poster without needing TMDB.
"""

import re
from dataclasses import dataclass
from urllib.parse import quote

import httpx

BASE_URL = "https://v3-cinemeta.strem.io"
TIMEOUT = httpx.Timeout(10.0)
TYPES = ("movie", "series")
YEAR_RE = re.compile(r"\d{4}")


@dataclass
class CinemetaTitle:
    imdb_id: str
    type: str
    name: str
    year: int | None
    poster: str


def poster_url(imdb_id: str) -> str:
    return f"https://images.metahub.space/poster/medium/{imdb_id}/img"


def _parse_year(meta: dict) -> int | None:
    for field in ("year", "releaseInfo"):
        match = YEAR_RE.search(str(meta.get(field) or ""))
        if match:
            return int(match.group())
    return None


def _to_title(meta: dict, type_: str) -> CinemetaTitle | None:
    imdb_id = meta.get("imdb_id") or meta.get("id")
    name = meta.get("name")
    if not imdb_id or not str(imdb_id).startswith("tt") or not name:
        return None
    return CinemetaTitle(
        imdb_id=imdb_id,
        type=meta.get("type") or type_,
        name=name,
        year=_parse_year(meta),
        poster=poster_url(imdb_id),
    )


def lookup(imdb_id: str) -> CinemetaTitle | None:
    """Find a title by IMDb ID, trying movie first, then series."""
    with httpx.Client(timeout=TIMEOUT) as client:
        for type_ in TYPES:
            response = client.get(f"{BASE_URL}/meta/{type_}/{imdb_id}.json")
            if response.status_code != 200:
                continue
            meta = (response.json() or {}).get("meta")
            if meta:
                title = _to_title(meta, type_)
                if title:
                    return title
    return None


def search(query: str, type_: str = "movie", limit: int = 20) -> list[CinemetaTitle]:
    """Search titles by name."""
    if type_ not in TYPES or not query.strip():
        return []
    url = f"{BASE_URL}/catalog/{type_}/top/search={quote(query.strip())}.json"
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.get(url)
    if response.status_code != 200:
        return []
    results = []
    for meta in (response.json() or {}).get("metas", []):
        title = _to_title(meta, type_)
        if title:
            results.append(title)
        if len(results) >= limit:
            break
    return results