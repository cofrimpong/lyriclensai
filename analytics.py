from __future__ import annotations

from collections import Counter
from itertools import combinations


def get_total_song_count(songs: list[dict]) -> int:
	return len(songs)


def get_genre_counts(songs: list[dict]) -> dict[str, int]:
	return dict(Counter(song["genre"] for song in songs))


def get_artist_counts(songs: list[dict]) -> dict[str, int]:
	return dict(Counter(song["artist"] for song in songs))


def get_mood_counts(songs: list[dict]) -> dict[str, int]:
	return dict(Counter(mood for song in songs for mood in song["moods"]))


def get_theme_counts(songs: list[dict]) -> dict[str, int]:
	return dict(Counter(theme for song in songs for theme in song["themes"]))


def get_era_counts(songs: list[dict]) -> dict[str, int]:
	return dict(Counter(get_era_display_label(song["era"]) for song in songs))


def get_theme_pair_counts(songs: list[dict]) -> dict[str, int]:
	pair_counts = Counter()
	for song in songs:
		unique_themes = sorted(set(song["themes"]))
		for left, right in combinations(unique_themes, 2):
			pair_counts[f"{left} + {right}"] += 1
	return dict(pair_counts)


def get_genre_family_counts(songs: list[dict]) -> dict[str, int]:
	return dict(Counter(get_genre_family(song["genre"]) for song in songs))


def get_featured_artist_spotlights(songs: list[dict], limit: int = 6) -> list[dict]:
	artist_groups: dict[str, list[dict]] = {}
	for song in songs:
		artist_groups.setdefault(song["artist"], []).append(song)

	ranked_artists = [label for label, _ in Counter(song["artist"] for song in songs).most_common(limit)]
	spotlight_map = {}
	for artist, artist_songs in artist_groups.items():
		sorted_songs = sorted(artist_songs, key=lambda item: item["title"])
		theme_counts = Counter(theme for song in sorted_songs for theme in song["themes"])
		spotlight_map[artist] = {
			"artist": artist,
			"songs": [song["title"] for song in sorted_songs[:2]],
			"genre": get_genre_family(sorted_songs[0]["genre"]),
			"emotional_lane": ", ".join(label for label, _ in theme_counts.most_common(3)),
			"spotify_artist_url": sorted_songs[0].get("spotify_artist_url", ""),
		}

	return [spotlight_map[artist] for artist in ranked_artists if artist in spotlight_map]


def get_genre_family(genre: str) -> str:
	normalized = genre.lower()
	if "k-pop" in normalized:
		return "K-Pop"
	if "afrobeats" in normalized:
		return "Afrobeats"
	if "r&b" in normalized or "neo soul" in normalized:
		return "R&B"
	if "hip-hop" in normalized or "rap" in normalized:
		return "Hip-Hop"
	if "soul" in normalized or "funk" in normalized:
		return "Soul/Funk"
	if "pop" in normalized:
		return "Pop"
	return genre.split("/")[0].strip()


def get_era_display_label(era: str) -> str:
	if "2020" in era:
		return "2020s"
	if "2010" in era:
		return "2010s"
	if "1980" in era:
		return "1980s"
	return era


def build_dashboard_snapshot(songs: list[dict], limit: int = 6) -> dict:
	artist_counts = get_artist_counts(songs)
	genre_counts = get_genre_counts(songs)
	genre_family_counts = get_genre_family_counts(songs)
	mood_counts = get_mood_counts(songs)
	theme_counts = get_theme_counts(songs)
	era_counts = get_era_counts(songs)
	theme_pair_counts = get_theme_pair_counts(songs)
	artist_spotlights = get_featured_artist_spotlights(songs, limit=limit)

	top_artist = max(artist_counts, key=artist_counts.get) if artist_counts else "N/A"
	top_theme = max(theme_counts, key=theme_counts.get) if theme_counts else "N/A"
	top_genre = max(genre_family_counts, key=genre_family_counts.get) if genre_family_counts else "N/A"
	top_era = max(era_counts, key=era_counts.get) if era_counts else "N/A"

	top_artists = Counter(artist_counts).most_common(limit)
	top_genres = Counter(genre_family_counts).most_common(limit)
	top_moods = Counter(mood_counts).most_common(limit)
	top_themes = Counter(theme_counts).most_common(limit)
	top_pairs = Counter(theme_pair_counts).most_common(limit)

	return {
		"stats": {
			"total_songs": get_total_song_count(songs),
			"artist_count": len(artist_counts),
			"genre_count": len(genre_counts),
			"era_count": len(era_counts),
			"theme_count": len(theme_counts),
			"top_artist": top_artist,
			"top_theme": top_theme,
			"top_genre": top_genre,
			"top_era": top_era,
		},
		"lists": {
			"artists": [{"label": label, "value": value} for label, value in top_artists],
			"genres": [{"label": label, "value": value} for label, value in top_genres],
			"moods": [{"label": label, "value": value} for label, value in top_moods],
			"themes": [{"label": label, "value": value} for label, value in top_themes],
			"theme_pairs": [{"label": label, "value": value} for label, value in top_pairs],
			"artist_spotlights": artist_spotlights,
		},
		"charts": {
			"artists": {
				"labels": [label for label, _ in top_artists],
				"values": [value for _, value in top_artists],
			},
			"genres": {
				"labels": [label for label, _ in top_genres],
				"values": [value for _, value in top_genres],
			},
			"moods": {
				"labels": [label for label, _ in top_moods],
				"values": [value for _, value in top_moods],
			},
			"themes": {
				"labels": [label for label, _ in top_themes],
				"values": [value for _, value in top_themes],
			},
			"eras": {
				"labels": list(era_counts.keys()),
				"values": list(era_counts.values()),
			},
			"theme_pairs": {
				"labels": [label for label, _ in top_pairs],
				"values": [value for _, value in top_pairs],
			},
		},
	}
