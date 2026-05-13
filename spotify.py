from __future__ import annotations

import base64
import json
import logging
import time
from pathlib import Path
from threading import Lock, Thread
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


LOGGER = logging.getLogger(__name__)
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_AUTH_BASE = "https://accounts.spotify.com"
REQUEST_TIMEOUT_SECONDS = 5
_CLIENT_TOKEN_LOCK = Lock()
_CLIENT_TOKEN_CACHE = {"access_token": "", "expires_at": 0.0}
_METADATA_CACHE_LOCK = Lock()
_METADATA_CACHE: dict[str, dict] | None = None
_WARMUP_LOCK = Lock()
_WARMUP_ACTIVE = False


def is_spotify_configured(config: dict) -> bool:
    return bool(config.get("SPOTIFY_CLIENT_ID") and config.get("SPOTIFY_CLIENT_SECRET"))


def get_spotify_cache_path(config: dict) -> Path:
    return Path(config["SPOTIFY_METADATA_CACHE_PATH"])


def extract_spotify_track_id(track_url: str) -> str:
    if not track_url:
        return ""

    if track_url.startswith("spotify:track:"):
        return track_url.rsplit(":", maxsplit=1)[-1].strip()

    parsed = urlparse(track_url)
    segments = [segment for segment in parsed.path.split("/") if segment]
    if "track" in segments:
        track_index = segments.index("track")
        if track_index + 1 < len(segments):
            return segments[track_index + 1].strip()

    return ""


def build_authorize_url(client_id: str, redirect_uri: str, state: str, scope: str) -> str:
    return f"{SPOTIFY_AUTH_BASE}/authorize?{urlencode({'response_type': 'code', 'client_id': client_id, 'scope': scope, 'redirect_uri': redirect_uri, 'state': state, 'show_dialog': 'true'})}"


def exchange_authorization_code(config: dict, code: str, redirect_uri: str) -> dict:
    return _post_token_request(
        config,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )


def refresh_user_token(config: dict, refresh_token: str) -> dict:
    return _post_token_request(
        config,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )


def fetch_current_user_profile(access_token: str) -> dict:
    if not access_token:
        return {}

    return _spotify_json_request(
        f"{SPOTIFY_API_BASE}/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def get_track_metadata(track_url: str, config: dict, allow_fetch: bool = True) -> dict:
    track_id = extract_spotify_track_id(track_url)
    if not track_id:
        return {}

    cache = _load_metadata_cache(config)
    cached = cache.get(track_id)
    if cached:
        return dict(cached)

    if not allow_fetch or not config.get("ENABLE_SPOTIFY_METADATA_FETCH"):
        return {}

    token = _get_client_access_token(config)
    if not token:
        return {}

    try:
        payload = _spotify_json_request(
            f"{SPOTIFY_API_BASE}/tracks/{track_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    except Exception:
        LOGGER.exception("Spotify track metadata lookup failed for track id %s.", track_id)
        return {}

    album = payload.get("album") or {}
    images = album.get("images") or []
    metadata = {
        "track_id": track_id,
        "album_art_url": images[0].get("url", "") if images else "",
        "album_name": album.get("name", ""),
        "track_name": payload.get("name", ""),
        "artist_names": [artist.get("name", "") for artist in payload.get("artists") or [] if artist.get("name")],
        "spotify_uri": payload.get("uri", ""),
        "fetched_at": int(time.time()),
    }
    _store_metadata_cache_entry(config, track_id, metadata)
    return metadata


def warm_metadata_cache_async(track_urls: list[str], config: dict) -> None:
    if not config.get("ENABLE_SPOTIFY_METADATA_FETCH") or not is_spotify_configured(config):
        return

    unique_track_urls = []
    seen_track_ids = set()
    for track_url in track_urls:
        track_id = extract_spotify_track_id(track_url)
        if not track_id or track_id in seen_track_ids:
            continue
        if _load_metadata_cache(config).get(track_id):
            continue
        seen_track_ids.add(track_id)
        unique_track_urls.append(track_url)

    if not unique_track_urls:
        return

    global _WARMUP_ACTIVE
    with _WARMUP_LOCK:
        if _WARMUP_ACTIVE:
            return
        _WARMUP_ACTIVE = True

    def _worker() -> None:
        global _WARMUP_ACTIVE
        try:
            for track_url in unique_track_urls:
                get_track_metadata(track_url, config, allow_fetch=True)
        finally:
            with _WARMUP_LOCK:
                _WARMUP_ACTIVE = False

    Thread(target=_worker, name="spotify-metadata-warmup", daemon=True).start()


def _post_token_request(config: dict, payload: dict) -> dict:
    client_id = config.get("SPOTIFY_CLIENT_ID", "")
    client_secret = config.get("SPOTIFY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return {}

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    body = urlencode(payload).encode("utf-8")
    return _spotify_json_request(
        f"{SPOTIFY_AUTH_BASE}/api/token",
        data=body,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )


def _get_client_access_token(config: dict) -> str:
    if not is_spotify_configured(config):
        return ""

    now = time.time()
    with _CLIENT_TOKEN_LOCK:
        cached_token = _CLIENT_TOKEN_CACHE.get("access_token", "")
        expires_at = float(_CLIENT_TOKEN_CACHE.get("expires_at", 0.0) or 0.0)
        if cached_token and expires_at > now + 30:
            return cached_token

    token_payload = _post_token_request(config, {"grant_type": "client_credentials"})
    access_token = token_payload.get("access_token", "")
    expires_in = int(token_payload.get("expires_in", 0) or 0)
    if not access_token:
        return ""

    with _CLIENT_TOKEN_LOCK:
        _CLIENT_TOKEN_CACHE["access_token"] = access_token
        _CLIENT_TOKEN_CACHE["expires_at"] = now + expires_in

    return access_token


def _spotify_json_request(url: str, headers: dict | None = None, data: bytes | None = None) -> dict:
    request = Request(url, headers=headers or {}, data=data)
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        LOGGER.warning("Spotify request failed with HTTP %s for %s: %s", exc.code, url, detail)
    except URLError as exc:
        LOGGER.warning("Spotify request failed for %s: %s", url, exc.reason)
    except TimeoutError:
        LOGGER.warning("Spotify request timed out for %s", url)
    except json.JSONDecodeError:
        LOGGER.warning("Spotify returned invalid JSON for %s", url)
    return {}


def _load_metadata_cache(config: dict) -> dict[str, dict]:
    global _METADATA_CACHE
    with _METADATA_CACHE_LOCK:
        if _METADATA_CACHE is not None:
            return _METADATA_CACHE

        cache_path = get_spotify_cache_path(config)
        if cache_path.exists():
            try:
                _METADATA_CACHE = json.loads(cache_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                LOGGER.warning("Spotify metadata cache could not be loaded from %s.", cache_path)
                _METADATA_CACHE = {}
        else:
            _METADATA_CACHE = {}

        return _METADATA_CACHE


def _store_metadata_cache_entry(config: dict, track_id: str, metadata: dict) -> None:
    with _METADATA_CACHE_LOCK:
        global _METADATA_CACHE
        if _METADATA_CACHE is None:
            _METADATA_CACHE = {}
        cache = _METADATA_CACHE
        cache[track_id] = metadata
        cache_path = get_spotify_cache_path(config)
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
        except OSError:
            LOGGER.warning("Spotify metadata cache could not be written to %s.", cache_path)
