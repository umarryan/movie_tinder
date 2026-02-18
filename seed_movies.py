"""One-off script to seed the DB with popular movies and their TMDB streaming availability.
Set TMDB_API_KEY in env or .env, then run: python seed_movies.py"""
import os
os.environ.setdefault("TMDB_API_KEY", os.environ.get("TMDB_API_KEY", ""))

from database import SessionLocal, init_db
from tmdb_sync import sync_movie_by_title

# Starter set of popular movies (title, year)
SEED_MOVIES = [
    ("Inception", 2010),
    ("The Dark Knight", 2008),
    ("Interstellar", 2014),
    ("The Shawshank Redemption", 1994),
    ("Pulp Fiction", 1994),
]

def main():
    init_db()
    db = SessionLocal()
    try:
        for title, year in SEED_MOVIES:
            m = sync_movie_by_title(db, title, year)
            print(f"Synced: {m.title}" if m else f"Skip (not found): {title} ({year})")
    finally:
        db.close()

if __name__ == "__main__":
    main()
