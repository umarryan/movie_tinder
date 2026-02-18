"""App configuration. TMDB API key via env TMDB_API_KEY or .env."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    tmdb_api_key: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_region: str = "US"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
