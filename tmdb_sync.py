"""Sync movie metadata and streaming availability from TMDB into local DB."""
from sqlalchemy.orm import Session

from database import Movie, StreamingService, MovieStreamingService
from tmdb_client import search_movie, get_watch_providers, get_movie_details, get_popular_movies


def sync_movie_from_tmdb(db: Session, movie_id: int) -> bool:
    """
    Sync a local movie by id: look up TMDB (by tmdb_id or search title/year),
    fetch watch providers, and update StreamingService / MovieStreamingService.
    Returns True if sync succeeded, False otherwise.
    """
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        return False

    tmdb_data = None
    if movie.tmdb_id:
        tmdb_data = get_movie_details(movie.tmdb_id)
    if not tmdb_data:
        result = search_movie(movie.title, movie.release_year)
        if not result:
            return False
        movie.tmdb_id = result["id"]
        movie.original_title = result.get("original_title")
        if result.get("overview") and not movie.description:
            movie.description = result["overview"]
        if result.get("poster_path") and not movie.poster_url:
            movie.poster_url = f"https://image.tmdb.org/t/p/w500{result['poster_path']}"
        if result.get("release_date"):
            try:
                movie.release_year = int(result["release_date"][:4])
            except (ValueError, TypeError):
                pass
        db.commit()
        tmdb_data = result

    tmdb_id = movie.tmdb_id or tmdb_data.get("id")
    if not tmdb_id:
        return False

    provider_names = get_watch_providers(tmdb_id)
    if not provider_names:
        return True  # no providers is still success

    # Remove existing movie–streaming links for this movie
    db.query(MovieStreamingService).filter(MovieStreamingService.movie_id == movie_id).delete()

    for name in provider_names:
        service = db.query(StreamingService).filter(StreamingService.name == name).first()
        if not service:
            service = StreamingService(name=name)
            db.add(service)
            db.flush()
        link = MovieStreamingService(movie_id=movie_id, streaming_service_id=service.id)
        db.add(link)

    db.commit()
    return True


def sync_movie_by_title(db: Session, title: str, year: int | None = None) -> Movie | None:
    """
    Search TMDB by title/year, create or update a local Movie, sync providers.
    Returns the local Movie or None.
    """
    result = search_movie(title, year)
    if not result:
        return None

    tmdb_id = result["id"]
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    if not movie:
        movie = db.query(Movie).filter(
            Movie.title == result.get("title"),
            Movie.release_year == (int(result["release_date"][:4]) if result.get("release_date") else None),
        ).first()
    if not movie:
        movie = Movie(
            title=result.get("title") or title,
            genre="Unknown",
            description=result.get("overview"),
            poster_url=f"https://image.tmdb.org/t/p/w500{result['poster_path']}" if result.get("poster_path") else None,
            release_year=int(result["release_date"][:4]) if result.get("release_date") else None,
            tmdb_id=tmdb_id,
            original_title=result.get("original_title"),
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)
    else:
        if not movie.tmdb_id:
            movie.tmdb_id = tmdb_id
            movie.original_title = result.get("original_title") or movie.original_title
            if result.get("overview") and not movie.description:
                movie.description = result.get("overview")
            if result.get("poster_path") and not movie.poster_url:
                movie.poster_url = f"https://image.tmdb.org/t/p/w500{result['poster_path']}"
            db.commit()
            db.refresh(movie)

    sync_movie_from_tmdb(db, movie.id)
    return movie


def sync_popular_movies(db: Session, page: int = 1) -> int:
    """
    Fetch a page of popular movies from TMDB and add any new ones to the local DB
    (with watch providers). Skips movies we already have by tmdb_id.
    Commits after each movie to avoid holding the DB lock and so other requests see new rows.
    Returns the number of new movies added.
    """
    results = get_popular_movies(page)
    if not results:
        return 0
    added = 0
    for item in results:
        tmdb_id = item.get("id")
        if not tmdb_id:
            continue
        existing = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
        if existing:
            continue
        title = item.get("title") or "Unknown"
        release_date = item.get("release_date")
        year = int(release_date[:4]) if release_date else None
        poster_path = item.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        movie = Movie(
            title=title,
            genre="Unknown",
            description=item.get("overview"),
            poster_url=poster_url,
            release_year=year,
            tmdb_id=tmdb_id,
            original_title=item.get("original_title"),
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)
        sync_movie_from_tmdb(db, movie.id)
        added += 1
    return added
