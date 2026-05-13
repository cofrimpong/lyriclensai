import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "lyriclens-sprint-1")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "")
    SPOTIFY_SCOPES = os.environ.get("SPOTIFY_SCOPES", "user-read-email user-read-private")
    SPOTIFY_METADATA_CACHE_PATH = os.environ.get(
        "SPOTIFY_METADATA_CACHE_PATH",
        str(BASE_DIR / "vector_db" / "spotify_metadata_cache.json"),
    )
    ENABLE_SPOTIFY_METADATA_FETCH = os.environ.get("ENABLE_SPOTIFY_METADATA_FETCH", "1") != "0" and "PYTEST_CURRENT_TEST" not in os.environ
