from hashlib import md5

from flask import Flask, abort, redirect, render_template, request, url_for

from analytics import build_dashboard_snapshot
from config import Config
from data_loader import load_songs
from search_engine import semantic_search
from vector_store import ensure_vector_collection, expand_genre_facets, get_related_songs


def get_corpus_facets(songs: list[dict]) -> dict:
    genres = expand_genre_facets(sorted({song["genre"] for song in songs}))
    eras = sorted({song["era"] for song in songs})
    artists = sorted({song["artist"] for song in songs})
    moods = sorted({mood for song in songs for mood in song["moods"]})
    return {
        "genres": genres,
        "eras": eras,
        "artists": artists,
        "moods": moods,
    }


def find_song(song_id: int, songs: list[dict]) -> dict | None:
    for song in songs:
        if song["id"] == song_id:
            return song
    return None


def build_related_preview(song: dict, songs: list[dict]) -> list[dict]:
    related = []
    song_themes = set(song["themes"])

    for candidate in songs:
        if candidate["id"] == song["id"]:
            continue

        overlap = len(song_themes.intersection(candidate["themes"]))
        if not overlap:
            continue

        related.append({**candidate, "overlap": overlap})

    related.sort(key=lambda item: item["overlap"], reverse=True)
    return related[:3]


def filter_song_catalog(songs: list[dict], filters: dict) -> list[dict]:
    filtered_songs = []

    for song in songs:
        if filters["genre"] and filters["genre"].casefold() not in song["genre"].casefold():
            continue
        if filters["mood"] and filters["mood"] not in song["moods"]:
            continue
        if filters["era"] and filters["era"] != song["era"]:
            continue
        if filters["artist"] and filters["artist"] != song["artist"]:
            continue

        filtered_songs.append(
            {
                **song,
                "explanation": "Catalog browse mode surfaces songs from the LyricLens library so you can explore the full collection.",
            }
        )

    return filtered_songs


def decorate_song(song: dict) -> dict:
    palette = build_song_palette(song)
    title_tokens = [token for token in song["title"].replace("-", " ").split() if token]
    artist_tokens = [token for token in song["artist"].split() if token]
    initials = "".join(token[0] for token in (title_tokens[:1] + artist_tokens[:1]) if token).upper()[:2] or song["title"][:2].upper()
    lyric_moment = song.get("lyric_moment") or song.get("safe_excerpt") or ""

    return {
        **song,
        "artwork_initials": initials,
        "artwork_style": (
            f"--artwork-start: {palette['start']};"
            f" --artwork-end: {palette['end']};"
            f" --artwork-glow: {palette['glow']};"
            f" --artwork-accent: {palette['accent']};"
        ),
        "lyric_moment": lyric_moment,
        "lyric_lens": song.get("lyric_lens", song.get("summary", "")),
    }


def decorate_song_collection(songs: list[dict]) -> list[dict]:
    return [decorate_song(song) for song in songs]


def build_song_palette(song: dict) -> dict:
    palettes = [
        {"start": "rgba(34, 211, 238, 0.92)", "end": "rgba(59, 130, 246, 0.82)", "glow": "rgba(34, 211, 238, 0.28)", "accent": "rgba(191, 219, 254, 0.9)"},
        {"start": "rgba(236, 72, 153, 0.94)", "end": "rgba(168, 85, 247, 0.82)", "glow": "rgba(236, 72, 153, 0.3)", "accent": "rgba(251, 207, 232, 0.92)"},
        {"start": "rgba(250, 204, 21, 0.9)", "end": "rgba(249, 115, 22, 0.82)", "glow": "rgba(250, 204, 21, 0.26)", "accent": "rgba(254, 240, 138, 0.92)"},
        {"start": "rgba(74, 222, 128, 0.9)", "end": "rgba(16, 185, 129, 0.82)", "glow": "rgba(52, 211, 153, 0.24)", "accent": "rgba(209, 250, 229, 0.92)"},
        {"start": "rgba(129, 140, 248, 0.92)", "end": "rgba(236, 72, 153, 0.78)", "glow": "rgba(129, 140, 248, 0.3)", "accent": "rgba(224, 231, 255, 0.94)"},
    ]
    digest = md5(f"{song['title']}|{song['artist']}|{song['genre']}".encode("utf-8")).hexdigest()
    return palettes[int(digest[:2], 16) % len(palettes)]


def build_homepage_rotating_lyrics(songs: list[dict]) -> list[dict]:
    curated_titles = ["Good Days", "Lonely At The Top", "Man in the Mirror", "Snooze", "Someone Like You"]
    selected = [song for song in songs if song["title"] in curated_titles]
    if len(selected) < 4:
        selected = songs[:5]
    return decorate_song_collection(selected[:5])


def build_discovery_rails(songs: list[dict]) -> list[dict]:
    sections = [
        ("Healing & Reflection", {"themes": {"healing", "growth", "reflection", "peace"}, "moods": {"reflective", "hopeful", "calm", "emotional"}}),
        ("Love & Intimacy", {"themes": {"love", "romance", "relationships", "connection"}, "moods": {"romantic", "warm", "intimate", "soft"}}),
        ("Confidence & Power", {"themes": {"confidence", "empowerment", "self-expression", "identity"}, "moods": {"confident", "bold", "powerful", "assertive"}}),
        ("Fame & Pressure", {"themes": {"fame", "pressure", "success", "artistry", "ambition"}, "moods": {"dramatic", "intense", "reflective", "motivational"}}),
        ("Celebration & Energy", {"themes": {"celebration", "energy", "freedom", "joy"}, "moods": {"upbeat", "party", "energetic", "vibrant"}}),
    ]

    rails = []
    for title, mapping in sections:
        picked = []
        for song in songs:
            theme_overlap = mapping["themes"].intersection({theme.casefold() for theme in song["themes"]})
            mood_overlap = mapping["moods"].intersection({mood.casefold() for mood in song["moods"]})
            if not theme_overlap and not mood_overlap:
                continue
            picked.append(song)

        if not picked:
            continue

        rails.append(
            {
                "title": title,
                "songs": decorate_song_collection(picked[:6]),
            }
        )

    return rails


def paginate_items(items: list[dict], page: int, page_size: int = 10) -> dict:
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    current_page = min(max(page, 1), total_pages)
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    return {
        "items": items[start_index:end_index],
        "current_page": current_page,
        "total_pages": total_pages,
        "total_items": total_items,
        "page_size": page_size,
    }


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/")
    def index():
        songs = load_songs()
        highlights = decorate_song_collection(songs[:4])
        rotating_lyrics = build_homepage_rotating_lyrics(songs)
        discovery_rails = build_discovery_rails(songs)
        return render_template(
            "index.html",
            highlights=highlights,
            total_songs=len(songs),
            rotating_lyrics=rotating_lyrics,
            discovery_rails=discovery_rails,
        )

    @app.route("/search", methods=["GET", "POST"])
    def search():
        songs = load_songs()
        facets = get_corpus_facets(songs)
        initial_query = request.args.get("q", "").strip()

        if request.method == "POST":
            query = request.form.get("query", "").strip()
            selected_filters = {
                "genre": request.form.get("genre", "").strip(),
                "mood": request.form.get("mood", "").strip(),
                "era": request.form.get("era", "").strip(),
                "artist": request.form.get("artist", "").strip(),
            }
            return redirect(url_for("results", q=query, **selected_filters))

        return render_template("search.html", facets=facets, initial_query=initial_query)

    @app.route("/results")
    def results():
        query = request.args.get("q", "").strip()
        songs = load_songs()
        page = request.args.get("page", default=1, type=int) or 1
        filters = {
            "genre": request.args.get("genre", "").strip(),
            "mood": request.args.get("mood", "").strip(),
            "era": request.args.get("era", "").strip(),
            "artist": request.args.get("artist", "").strip(),
        }
        search_results = semantic_search(query, filters=filters, top_k=len(songs)) if query else filter_song_catalog(songs, filters)
        search_results = decorate_song_collection(search_results)
        pagination = paginate_items(search_results, page=page, page_size=10)
        return render_template(
            "results.html",
            query=query,
            results=pagination["items"],
            filters=filters,
            current_page=pagination["current_page"],
            total_pages=pagination["total_pages"],
            total_results=pagination["total_items"],
        )

    @app.route("/dashboard")
    def dashboard():
        songs = load_songs()
        snapshot = build_dashboard_snapshot(songs)
        return render_template(
            "dashboard.html",
            stats=snapshot["stats"],
            charts=snapshot["charts"],
            lists=snapshot["lists"],
        )

    @app.post("/warmup")
    def warmup():
        ensure_vector_collection(songs=load_songs())
        return ("", 204)

    @app.route("/songs/<int:song_id>")
    def song_detail(song_id: int):
        songs = load_songs()
        song = find_song(song_id, songs)
        if song is None:
            abort(404)

        decorated_song = decorate_song(song)
        related_songs = decorate_song_collection(get_related_songs(song_id, top_k=3))
        return render_template("song_detail.html", song=decorated_song, related_songs=related_songs)

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
