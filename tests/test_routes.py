from app import create_app


def test_core_routes_load():
    app = create_app()
    client = app.test_client()

    for route in ["/", "/search", "/results", "/dashboard", "/about", "/songs/1"]:
        response = client.get(route)
        assert response.status_code == 200


def test_results_route_handles_real_search_query():
    app = create_app()
    client = app.test_client()

    response = client.get("/results?q=confidence+and+empowerment")
    assert response.status_code == 200
    assert b"Savage" in response.data
    assert b"Open in Spotify" in response.data
    assert b"Weak Match" not in response.data
    assert b"How LyricLens finds related songs" in response.data


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
    assert b"Open track in Spotify" in response.data
    assert b"View artist on Spotify" in response.data


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
