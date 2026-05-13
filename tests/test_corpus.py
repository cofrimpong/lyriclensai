from data_loader import REQUIRED_SONG_FIELDS, load_songs


def test_songs_json_loads_correctly():
    songs = load_songs()
    assert isinstance(songs, list)
    assert len(songs) == 20


def test_each_song_has_required_fields():
    songs = load_songs()
    for song in songs:
        assert REQUIRED_SONG_FIELDS.issubset(song.keys())


def test_every_song_has_required_spotify_and_metadata_fields():
    songs = load_songs()
    for song in songs:
        for key in ["title", "artist", "genre", "era", "spotify_track_url", "spotify_artist_url"]:
            assert song[key].strip()
        assert song["themes"]
        assert song["moods"]


def test_no_song_has_missing_id_title_or_artist():
    songs = load_songs()
    for song in songs:
        assert song["id"]
        assert song["title"].strip()
        assert song["artist"].strip()


def test_search_text_exists_for_every_song():
    songs = load_songs()
    assert all(song["search_text"].strip() for song in songs)


def test_no_full_lyrics_are_included():
    songs = load_songs()
    for song in songs:
        assert "\n" not in song["safe_excerpt"]
        assert len(song["safe_excerpt"]) <= 120
        assert len(song["summary"]) <= 260