from flask import Flask, abort, redirect, render_template, request, url_for

from analytics import build_dashboard_snapshot
from config import Config
from data_loader import load_songs
from search_engine import semantic_search
from vector_store import build_vector_collection, expand_genre_facets, get_related_songs


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


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/")
    def index():
        songs = load_songs()
        highlights = songs[:4]
        return render_template("index.html", highlights=highlights, total_songs=len(songs))

    @app.route("/search", methods=["GET", "POST"])
    def search():
        songs = load_songs()
        facets = get_corpus_facets(songs)

        if request.method == "POST":
            query = request.form.get("query", "").strip()
            selected_filters = {
                "genre": request.form.get("genre", "").strip(),
                "mood": request.form.get("mood", "").strip(),
                "era": request.form.get("era", "").strip(),
                "artist": request.form.get("artist", "").strip(),
            }
            return redirect(url_for("results", q=query, **selected_filters))

        return render_template("search.html", facets=facets)

    @app.route("/results")
    def results():
        query = request.args.get("q", "").strip()
        filters = {
            "genre": request.args.get("genre", "").strip(),
            "mood": request.args.get("mood", "").strip(),
            "era": request.args.get("era", "").strip(),
            "artist": request.args.get("artist", "").strip(),
        }
        search_results = semantic_search(query, filters=filters, top_k=6) if query else []
        return render_template("results.html", query=query, results=search_results, filters=filters)

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

    @app.route("/songs/<int:song_id>")
    def song_detail(song_id: int):
        songs = load_songs()
        song = find_song(song_id, songs)
        if song is None:
            abort(404)

        build_vector_collection(songs=songs)
        related_songs = get_related_songs(song_id, top_k=3)
        return render_template("song_detail.html", song=song, related_songs=related_songs)

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
