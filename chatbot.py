from __future__ import annotations

import logging
import re
from collections import Counter

from data_loader import load_songs
from search_engine import semantic_search


LOGGER = logging.getLogger(__name__)
TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "song",
    "songs",
    "that",
    "the",
    "to",
    "want",
    "with",
}


def build_chat_response(query: str) -> dict:
    songs = load_songs()
    cleaned_query = " ".join(query.split())
    if not cleaned_query:
        return {
            "answer": "Ask about moods, lyrics, themes, artists, or recommendations, and I will answer only from the current LyricLens music library.",
            "matches": [],
        }

    lower_query = cleaned_query.casefold()

    if "how many" in lower_query and ("songs" in lower_query or "library" in lower_query):
        artist_count = len({song["artist"] for song in songs})
        mood_count = len({mood for song in songs for mood in song["moods"]})
        return {
            "answer": f"The current LyricLens music library includes {len(songs)} songs from {artist_count} artists across {mood_count} moods.",
            "matches": [],
        }

    artist_matches = [song for song in songs if song["artist"].casefold() in lower_query]
    if artist_matches:
        unique_titles = [song["title"] for song in artist_matches[:4]]
        answer = f"Inside the current LyricLens music library, I can see {artist_matches[0]['artist']} on {', '.join(unique_titles)}."
        return {
            "answer": answer,
            "matches": [_song_match_payload(song, reason="Artist match from the current LyricLens library.") for song in artist_matches[:3]],
        }

    theme_summary = _build_theme_summary(lower_query, songs)
    if theme_summary:
        return theme_summary

    try:
        semantic_matches = semantic_search(cleaned_query, top_k=min(3, len(songs)))
    except Exception:
        LOGGER.exception("Chat semantic search failed for query '%s'.", cleaned_query)
        semantic_matches = []

    if semantic_matches:
        matches = [_song_match_payload(song) for song in semantic_matches[:3]]
        answer = "From the current LyricLens music library, these songs are the closest fit for that feeling or question."
        return {"answer": answer, "matches": matches}

    lexical_matches = _find_lexical_matches(cleaned_query, songs)
    if lexical_matches:
        return {
            "answer": "I could not find a strong semantic match, but these songs from the current LyricLens music library share your wording most closely.",
            "matches": [_song_match_payload(song, reason="Closest wording overlap in the current LyricLens library.") for song in lexical_matches[:3]],
        }

    return {
        "answer": "I can only answer from the current LyricLens music library, and I am not confident that this question maps to a song, mood, artist, or theme in the dataset yet.",
        "matches": [],
    }


def _build_theme_summary(lower_query: str, songs: list[dict]) -> dict | None:
    tokens = [token for token in TOKEN_PATTERN.findall(lower_query) if token not in STOPWORDS]
    if not tokens:
        return None

    mood_counter = Counter()
    theme_counter = Counter()
    matching_songs = []
    for song in songs:
        searchable_values = {song["genre"].casefold(), song["era"].casefold(), song["artist"].casefold()}
        searchable_values.update(item.casefold() for item in song["moods"])
        searchable_values.update(item.casefold() for item in song["themes"])
        if not any(token in value for token in tokens for value in searchable_values):
            continue

        matching_songs.append(song)
        mood_counter.update(mood.casefold() for mood in song["moods"])
        theme_counter.update(theme.casefold() for theme in song["themes"])

    if not matching_songs:
        return None

    top_moods = ", ".join(label for label, _ in mood_counter.most_common(3))
    top_themes = ", ".join(label for label, _ in theme_counter.most_common(3))
    answer = f"Within the current LyricLens music library, that topic shows up most around moods like {top_moods} and themes like {top_themes}."
    return {
        "answer": answer,
        "matches": [_song_match_payload(song) for song in matching_songs[:3]],
    }


def _find_lexical_matches(query: str, songs: list[dict]) -> list[dict]:
    query_tokens = {token for token in TOKEN_PATTERN.findall(query.casefold()) if token not in STOPWORDS}
    if not query_tokens:
        return []

    scored = []
    for song in songs:
        song_tokens = set(TOKEN_PATTERN.findall(song["search_text"].casefold()))
        overlap = len(query_tokens.intersection(song_tokens))
        if overlap:
            scored.append((overlap, song))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [song for _, song in scored]


def _song_match_payload(song: dict, reason: str | None = None) -> dict:
    default_reason = f"{song['title']} by {song['artist']} carries moods like {', '.join(song['moods'][:2])} and themes like {', '.join(song['themes'][:2])}."
    return {
        "id": song["id"],
        "title": song["title"],
        "artist": song["artist"],
        "lyric_moment": song["lyric_moment"],
        "reason": reason or default_reason,
    }
