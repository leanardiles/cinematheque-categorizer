"""Client for TMDB: lookup by IMDb ID, search, and original titles.

The display name is the original title when it uses the Latin alphabet,
otherwise the English title. Both are kept so the choice can be changed later.
"""

import re
import unicodedata
from dataclasses import dataclass

import httpx

from app.config import settings

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/w500"
TIMEOUT = httpx.Timeout(10.0)
TYPES = ("movie", "series")
YEAR_RE = re.compile(r"\d{4}")


@dataclass
class TmdbTitle:
    tmdb_id: int
    imdb_id: str | None  # None in search results until resolved
    type: str  # "movie" or "series" (Stremio's naming)
    original_title: str
    english_name: str | None
    original_language: str | None
    year: int | None
    poster: str | None

    @property
    def display_name(self) -> str:
        return display_name(self.original_title, self.english_name)


def is_latin(text: str) -> bool:
    """True if every letter in the text is from the Latin alphabet (accents included)."""
    for char in text:
        if char.isalpha() and "LATIN" not in unicodedata.name(char, ""):
            return False
    return True


def display_name(original: str, english: str | None) -> str:
    if original and is_latin(original):
        return original
    return english or original


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        timeout=TIMEOUT,
        headers={
            "Authorization": f"Bearer {settings.tmdb_read_token}",
            "Accept": "application/json",
        },
    )


def _year(date: str | None) -> int | None:
    match = YEAR_RE.match(date or "")
    return int(match.group()) if match else None


def _poster(path: str | None) -> str | None:
    return f"{IMAGE_URL}{path}" if path else None


def _from_movie(data: dict, imdb_id: str | None = None) -> TmdbTitle:
    return TmdbTitle(
        tmdb_id=data["id"],
        imdb_id=imdb_id,
        type="movie",
        original_title=data.get("original_title") or data.get("title") or "",
        english_name=data.get("title"),
        original_language=data.get("original_language"),
        year=_year(data.get("release_date")),
        poster=_poster(data.get("poster_path")),
    )


def _from_tv(data: dict, imdb_id: str | None = None) -> TmdbTitle:
    return TmdbTitle(
        tmdb_id=data["id"],
        imdb_id=imdb_id,
        type="series",
        original_title=data.get("original_name") or data.get("name") or "",
        english_name=data.get("name"),
        original_language=data.get("original_language"),
        year=_year(data.get("first_air_date")),
        poster=_poster(data.get("poster_path")),
    )


def lookup(imdb_id: str) -> TmdbTitle | None:
    """Find a film or series by IMDb ID."""
    with _client() as client:
        response = client.get(
            f"/find/{imdb_id}",
            params={"external_source": "imdb_id", "language": "en-US"},
        )
    if response.status_code != 200:
        return None
    data = response.json()
    if data.get("movie_results"):
        return with_original_poster(_from_movie(data["movie_results"][0], imdb_id))
    if data.get("tv_results"):
        return with_original_poster(_from_tv(data["tv_results"][0], imdb_id))
    return None


def search(query: str, type_: str = "movie", limit: int = 20) -> list[TmdbTitle]:
    """Search by title; matches original and English titles. Results have no IMDb ID yet."""
    if type_ not in TYPES or not query.strip():
        return []
    endpoint = "/search/movie" if type_ == "movie" else "/search/tv"
    with _client() as client:
        response = client.get(
            endpoint,
            params={"query": query.strip(), "include_adult": "false", "language": "en-US"},
        )
    if response.status_code != 200:
        return []
    convert = _from_movie if type_ == "movie" else _from_tv
    return [convert(item) for item in response.json().get("results", [])[:limit]]


def resolve(tmdb_id: int, type_: str) -> TmdbTitle | None:
    """Fetch full details for a search result, including its IMDb ID."""
    if type_ not in TYPES:
        return None
    path = f"/movie/{tmdb_id}" if type_ == "movie" else f"/tv/{tmdb_id}"
    with _client() as client:
        response = client.get(
            path, params={"append_to_response": "external_ids", "language": "en-US"}
        )
    if response.status_code != 200:
        return None
    data = response.json()
    imdb_id = data.get("imdb_id") or (data.get("external_ids") or {}).get("imdb_id")
    if not imdb_id:
        return None  # Stremio needs an IMDb ID, so titles without one can't be added
    title = _from_movie(data, imdb_id) if type_ == "movie" else _from_tv(data, imdb_id)
    return with_original_poster(title)


def original_poster(tmdb_id: int, type_: str, language: str | None) -> str | None:
    """The best-rated poster in the film's original language, or None if there isn't one."""
    if not language or type_ not in TYPES:
        return None
    path = f"/movie/{tmdb_id}/images" if type_ == "movie" else f"/tv/{tmdb_id}/images"
    with _client() as client:
        response = client.get(path, params={"include_image_language": language})
    if response.status_code != 200:
        return None
    posters = [p for p in response.json().get("posters", []) if p.get("iso_639_1") == language]
    if not posters:
        return None
    best = max(posters, key=lambda p: (p.get("vote_average", 0), p.get("vote_count", 0)))
    return _poster(best.get("file_path"))


def with_original_poster(title: TmdbTitle) -> TmdbTitle:
    """Swap in the original-language poster when the display name is the original title."""
    if is_latin(title.original_title):
        title.poster = (
            original_poster(title.tmdb_id, title.type, title.original_language) or title.poster
        )
    return title    