from analytics import build_dashboard_snapshot, get_artist_counts, get_era_counts, get_genre_counts, get_mood_counts, get_theme_counts, get_total_song_count, get_theme_pair_counts
from data_loader import load_songs


def test_total_song_count_matches_corpus():
	songs = load_songs()
	assert get_total_song_count(songs) == 20


def test_genre_counts_return_dictionary():
	songs = load_songs()
	genre_counts = get_genre_counts(songs)
	assert isinstance(genre_counts, dict)
	assert genre_counts["Hip-Hop / Rap"] == 2


def test_artist_counts_return_dictionary():
	songs = load_songs()
	artist_counts = get_artist_counts(songs)
	assert isinstance(artist_counts, dict)
	assert artist_counts["Megan Thee Stallion"] == 2


def test_mood_counts_return_dictionary():
	songs = load_songs()
	mood_counts = get_mood_counts(songs)
	assert isinstance(mood_counts, dict)
	assert mood_counts["emotional"] >= 1


def test_theme_counts_return_dictionary():
	songs = load_songs()
	theme_counts = get_theme_counts(songs)
	assert isinstance(theme_counts, dict)
	assert theme_counts["confidence"] >= 1


def test_era_counts_return_dictionary():
	songs = load_songs()
	era_counts = get_era_counts(songs)
	assert isinstance(era_counts, dict)
	assert era_counts["2020s"] >= 1


def test_theme_pair_counts_return_dictionary():
	songs = load_songs()
	pair_counts = get_theme_pair_counts(songs)
	assert isinstance(pair_counts, dict)
	assert "confidence + self-expression" in pair_counts


def test_build_dashboard_snapshot_returns_chart_payloads():
	songs = load_songs()
	snapshot = build_dashboard_snapshot(songs)
	assert snapshot["stats"]["total_songs"] == 20
	assert snapshot["stats"]["theme_count"] >= 1
	assert "artists" in snapshot["charts"]
	assert "genres" in snapshot["charts"]
	assert "theme_pairs" in snapshot["charts"]
	assert snapshot["lists"]["artist_spotlights"]
	assert len(snapshot["charts"]["theme_pairs"]["labels"]) == len(snapshot["charts"]["theme_pairs"]["values"])
