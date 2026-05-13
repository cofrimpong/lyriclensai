from app import create_app


def test_core_routes_load():
    app = create_app()
    client = app.test_client()

    for route in ["/", "/search", "/results", "/dashboard", "/about", "/songs/1", "/chat"]:
        response = client.get(route)
        assert response.status_code == 200


def test_results_route_handles_real_search_query():
    app = create_app()
    client = app.test_client()

    response = client.get("/results?q=confidence+and+empowerment")
    assert response.status_code == 200
    assert b"Savage" in response.data
    assert b"Listen on Spotify" in response.data
    assert b"LyricLens Interpretation" in response.data
    assert b"Explore Similar Songs" in response.data


def test_results_route_shows_catalog_for_blank_query():
    app = create_app()
    client = app.test_client()

    response = client.get("/results")
    assert response.status_code == 200
    assert b"Browsing the full LyricLens song library" in response.data
    assert b"Savage" in response.data
    assert b"No songs matched those filters" not in response.data
    assert response.data.count(b"Explore Similar Songs") == 10
    assert b">2</a>" in response.data


def test_results_route_supports_second_page_for_catalog_browse():
    app = create_app()
    client = app.test_client()

    response = client.get("/results?page=2")
    assert response.status_code == 200
    assert response.data.count(b"Explore Similar Songs") == 10
    assert b"Showing: 10 of 20" in response.data


def test_search_form_post_redirects_to_results():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/search",
        data={
            "query": "confidence and self-worth",
            "genre": "R&B",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/results?q=confidence+and+self-worth&genre=R%26B" in response.headers["Location"]


def test_search_route_prefills_query_from_get_params():
    app = create_app()
    client = app.test_client()

    response = client.get("/search?q=heartbreak+healing")
    assert response.status_code == 200
    assert b">heartbreak healing</textarea>" in response.data


def test_homepage_uses_mood_first_copy_without_stack_language():
    app = create_app()
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert b"Find songs by feeling, not just by title." in response.data
    assert b"View Mood Dashboard" in response.data
    assert b"Lyric Lens Moment" in response.data
    assert b"/warmup" not in response.data
    assert b"Connect Spotify" in response.data
    assert b"Chat" in response.data
    assert b"Technology Preview" not in response.data
    assert b"ChromaDB" not in response.data
    assert b"BERT" not in response.data


def test_results_route_respects_filter_query_params():
    app = create_app()
    client = app.test_client()

    response = client.get("/results?q=healing+and+reflection&genre=R%26B")
    assert response.status_code == 200
    assert b"Good Days" in response.data


def test_song_detail_route_exposes_spotify_actions():
    app = create_app()
    client = app.test_client()

    response = client.get("/songs/1")
    assert response.status_code == 200
    assert b"Listen on Spotify" in response.data
    assert b"Artist on Spotify" in response.data
    assert b"LyricLens Interpretation" in response.data


def test_song_detail_route_renders_album_art_when_spotify_metadata_is_available(monkeypatch):
    monkeypatch.setattr("app.is_spotify_configured", lambda config: True)
    monkeypatch.setattr(
        "app.get_track_metadata",
        lambda *args, **kwargs: {
            "album_art_url": "https://images.example.test/album.jpg",
            "album_name": "Test Album",
            "spotify_uri": "spotify:track:test",
        },
    )

    app = create_app()
    client = app.test_client()

    response = client.get("/songs/1")

    assert response.status_code == 200
    assert b"images.example.test/album.jpg" in response.data
    assert b"Album: Test Album" in response.data


def test_spotify_connect_redirects_to_spotify_authorize(monkeypatch):
    monkeypatch.setattr("app.is_spotify_configured", lambda config: True)
    monkeypatch.setattr("app.build_authorize_url", lambda *args, **kwargs: "https://accounts.spotify.com/authorize?client_id=test")

    app = create_app()
    app.config["SPOTIFY_REDIRECT_URI"] = "https://example.com/spotify/callback"
    client = app.test_client()

    response = client.get("/spotify/connect")

    assert response.status_code == 302
    assert response.headers["Location"] == "https://accounts.spotify.com/authorize?client_id=test"


def test_spotify_connect_shows_setup_screen_without_explicit_redirect_uri(monkeypatch):
    monkeypatch.setattr("app.is_spotify_configured", lambda config: True)

    app = create_app()
    app.config["SPOTIFY_REDIRECT_URI"] = ""
    client = app.test_client()

    response = client.get("/spotify/connect")

    assert response.status_code == 200
    assert b"Connect Spotify needs one callback URL configured first" in response.data
    assert b"SPOTIFY_REDIRECT_URI=" in response.data
    assert b"/spotify/callback" in response.data


def test_spotify_callback_stores_user_session(monkeypatch):
    monkeypatch.setattr(
        "app.exchange_authorization_code",
        lambda *args, **kwargs: {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
        },
    )
    monkeypatch.setattr(
        "app.fetch_current_user_profile",
        lambda access_token: {
            "display_name": "Test Listener",
            "external_urls": {"spotify": "https://open.spotify.com/user/test-listener"},
            "images": [],
        },
    )

    app = create_app()
    client = app.test_client()

    with client.session_transaction() as session_state:
        session_state["spotify_oauth_state"] = "expected-state"

    response = client.get("/spotify/callback?code=spotify-code&state=expected-state")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session_state:
        assert session_state["spotify_user"]["display_name"] == "Test Listener"
        assert session_state["spotify_token"]["access_token"] == "access-token"


def test_chat_api_returns_dataset_bounded_response(monkeypatch):
    monkeypatch.setattr(
        "app.build_chat_response",
        lambda query: {
            "answer": "I can only answer from the current LyricLens music library.",
            "matches": [{"id": 1, "title": "Good Days", "artist": "SZA", "reason": "Match from the dataset.", "lyric_moment": "Good day in my mind"}],
        },
    )

    app = create_app()
    client = app.test_client()

    response = client.post("/api/chat", json={"query": "songs for healing"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["answer"] == "I can only answer from the current LyricLens music library."
    assert payload["matches"][0]["title"] == "Good Days"


def test_dashboard_route_uses_mood_intelligence_messaging():
    app = create_app()
    client = app.test_client()

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Music Mood Intelligence Dashboard" in response.data
    assert b"Start With a Feeling" in response.data
    assert b"How LyricLens AI Finds Meaning" in response.data
    assert b"Explore this artist" in response.data
    assert b"Search this energy" in response.data
