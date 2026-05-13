from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


REQUIRED_SONG_FIELDS = {
	"spotify_track_url",
	"spotify_artist_url",
	"id",
	"title",
	"artist",
	"genre",
	"era",
	"themes",
	"moods",
	"lyric_moment",
	"lyric_lens",
	"summary",
	"safe_excerpt",
	"search_text",
}

RAW_REQUIRED_SONG_FIELDS = {
	"title",
	"artist",
	"genre",
	"era",
	"spotify_track_url",
	"spotify_artist_url",
	"themes",
	"moods",
	"lyric_moment",
	"lyric_lens",
}


def get_corpus_path() -> Path:
	return Path(__file__).resolve().parent / "_corpus" / "songs.json"


@lru_cache(maxsize=4)
def load_songs(file_path: str | Path | None = None) -> list[dict]:
	corpus_path = Path(file_path) if file_path else get_corpus_path()

	with corpus_path.open("r", encoding="utf-8") as file_handle:
		raw_songs = json.load(file_handle)

	validate_raw_song_collection(raw_songs)
	songs = normalize_song_collection(raw_songs)
	validate_song_collection(songs)
	return songs


def validate_raw_song_collection(songs: list[dict]) -> None:
	if not isinstance(songs, list):
		raise ValueError("Corpus must be a list of song records.")

	for song in songs:
		if not isinstance(song, dict):
			raise ValueError("Each raw song record must be a dictionary.")

		missing_fields = RAW_REQUIRED_SONG_FIELDS.difference(song.keys())
		if missing_fields:
			missing_list = ", ".join(sorted(missing_fields))
			raise ValueError(f"Raw song record is missing required fields: {missing_list}")

		for key in ["title", "artist", "genre", "era", "spotify_track_url", "spotify_artist_url", "lyric_moment", "lyric_lens"]:
			if not isinstance(song[key], str) or not song[key].strip():
				raise ValueError(f"Raw song field '{key}' must be a non-empty string.")

		for key in ["themes", "moods"]:
			if not isinstance(song[key], list) or not song[key]:
				raise ValueError(f"Raw song field '{key}' must be a non-empty list.")
			if not all(isinstance(item, str) and item.strip() for item in song[key]):
				raise ValueError(f"Raw song field '{key}' must contain non-empty strings.")


def normalize_song_collection(raw_songs: list[dict]) -> list[dict]:
	normalized_songs = []
	for index, song in enumerate(raw_songs, start=1):
		themes = [theme.strip() for theme in song["themes"] if isinstance(theme, str) and theme.strip()]
		moods = [mood.strip() for mood in song["moods"] if isinstance(mood, str) and mood.strip()]
		lyric_moment = song["lyric_moment"].strip()
		lyric_lens = song["lyric_lens"].strip()
		summary = song.get("summary") or build_summary(song["title"], song["artist"], song["genre"], song["era"], themes, moods)
		safe_excerpt = (song.get("safe_excerpt") or lyric_moment).strip()
		search_text = song.get("search_text") or build_search_text(
			song["title"],
			song["artist"],
			song["genre"],
			song["era"],
			themes,
			moods,
			lyric_moment,
			lyric_lens,
			summary,
		)

		normalized_songs.append(
			{
				"id": index,
				"title": song["title"].strip(),
				"artist": song["artist"].strip(),
				"genre": song["genre"].strip(),
				"era": song["era"].strip(),
				"spotify_track_url": song["spotify_track_url"].strip(),
				"spotify_artist_url": song["spotify_artist_url"].strip(),
				"themes": themes,
				"moods": moods,
				"lyric_moment": lyric_moment,
				"lyric_lens": lyric_lens,
				"summary": summary,
				"safe_excerpt": safe_excerpt.strip(),
				"search_text": search_text,
			}
		)

	return normalized_songs


def build_summary(title: str, artist: str, genre: str, era: str, themes: list[str], moods: list[str]) -> str:
	theme_text = ", ".join(themes[:3])
	mood_text = ", ".join(moods[:3])
	return f"{title} by {artist} is a {genre} track from the {era} centered on {theme_text} with a {mood_text} emotional profile."


def build_search_text(
	title: str,
	artist: str,
	genre: str,
	era: str,
	themes: list[str],
	moods: list[str],
	lyric_moment: str,
	lyric_lens: str,
	summary: str,
) -> str:
	segments = [
		lyric_moment,
		lyric_lens,
		" ".join(themes),
		" ".join(moods),
		title,
		artist,
		genre,
		era,
		summary,
	]
	return " ".join(segment.strip() for segment in segments if segment and segment.strip())


def validate_song_collection(songs: list[dict]) -> None:
	if not isinstance(songs, list):
		raise ValueError("Corpus must be a list of song records.")

	seen_ids: set[int] = set()
	for song in songs:
		validate_song(song)

		song_id = song["id"]
		if song_id in seen_ids:
			raise ValueError(f"Duplicate song id found: {song_id}")
		seen_ids.add(song_id)


def validate_song(song: dict) -> None:
	if not isinstance(song, dict):
		raise ValueError("Each song record must be a dictionary.")

	missing_fields = REQUIRED_SONG_FIELDS.difference(song.keys())
	if missing_fields:
		missing_list = ", ".join(sorted(missing_fields))
		raise ValueError(f"Song record is missing required fields: {missing_list}")

	if not isinstance(song["id"], int):
		raise ValueError("Song id must be an integer.")

	for key in ["title", "artist", "genre", "era", "summary", "search_text", "spotify_track_url", "spotify_artist_url", "lyric_moment", "lyric_lens"]:
		if not isinstance(song[key], str) or not song[key].strip():
			raise ValueError(f"Song field '{key}' must be a non-empty string.")

	if not isinstance(song["safe_excerpt"], str):
		raise ValueError("Song field 'safe_excerpt' must be a string.")

	for key in ["themes", "moods"]:
		if not isinstance(song[key], list) or not song[key]:
			raise ValueError(f"Song field '{key}' must be a non-empty list.")
		if not all(isinstance(item, str) and item.strip() for item in song[key]):
			raise ValueError(f"Song field '{key}' must contain non-empty strings.")
