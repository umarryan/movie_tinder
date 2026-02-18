"""TMDB API client: search movies and fetch watch/providers (streaming availability)."""
import httpx
from typing import Optional

from config import settings

# Normalize TMDB provider names to our StreamingService.name values (title case, common names)
PROVIDER_NAME_MAP = {
    "netflix": "Netflix",
    "hulu": "Hulu",
    "amazon prime video": "Amazon Prime Video",
    "amazon video": "Amazon Prime Video",
    "prime video": "Amazon Prime Video",
    "disney plus": "Disney+",
    "disney+": "Disney+",
    "hbo max": "HBO Max",
    "max": "Max",
    "peacock": "Peacock",
    "paramount+": "Paramount+",
    "paramount plus": "Paramount+",
    "apple tv plus": "Apple TV+",
    "apple tv+": "Apple TV+",
    "starz": "Starz",
    "showtime": "Showtime",
    "mubi": "Mubi",
    "criterion channel": "Criterion Channel",
    "crunchyroll": "Crunchyroll",
}


def _normalize_provider_name(raw: str) -> str:
    """Map TMDB provider name to our canonical StreamingService name."""
    key = raw.lower().strip()
    return PROVIDER_NAME_MAP.get(key, raw.strip())


def search_movie(title: str, year: Optional[int] = None) -> Optional[dict]:
    """
    Search TMDB for a movie by title (and optional year).
    Returns first result with id, title, overview, release_date, poster_path, etc., or None.
    """
    if not settings.tmdb_api_key:
        return None
    params = {"api_key": settings.tmdb_api_key, "query": title}
    if year is not None:
        params["year"] = year
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                f"{settings.tmdb_base_url}/search/movie",
                params=params,
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("results") or []
            if not results:
                return None
            return results[0]
    except Exception:
        return None


def get_watch_providers(tmdb_movie_id: int) -> list[str]:
    """
    Fetch watch providers for a TMDB movie ID for the configured region.
    Returns list of canonical streaming service names (flatrate/subscription only).
    """
    if not settings.tmdb_api_key:
        return []
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                f"{settings.tmdb_base_url}/movie/{tmdb_movie_id}/watch/providers",
                params={"api_key": settings.tmdb_api_key},
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("results") or {}
            region_data = results.get(settings.tmdb_region) or {}
            flatrate = region_data.get("flatrate") or []
            names = []
            for p in flatrate:
                name = (p.get("provider_name") or "").strip()
                if name:
                    names.append(_normalize_provider_name(name))
            return list(dict.fromkeys(names))  # unique, order preserved
    except Exception:
        return []


def get_movie_details(tmdb_movie_id: int) -> Optional[dict]:
    """Fetch movie details (title, overview, poster, release_date, etc.) by TMDB id."""
    if not settings.tmdb_api_key:
        return None
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                f"{settings.tmdb_base_url}/movie/{tmdb_movie_id}",
                params={"api_key": settings.tmdb_api_key},
            )
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def get_popular_movies(page: int = 1) -> list[dict]:
    """
    Fetch a page of popular movies from TMDB.
    Returns list of dicts with id, title, overview, release_date, poster_path, etc.
    """
    if not settings.tmdb_api_key:
        return []
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(
                f"{settings.tmdb_base_url}/movie/popular",
                params={"api_key": settings.tmdb_api_key, "page": page},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("results") or []
    except Exception:
        return []
