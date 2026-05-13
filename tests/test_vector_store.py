import numpy as np

import vector_store
from data_loader import load_songs
from vector_store import build_vector_collection, expand_genre_facets, get_related_songs, initialize_vector_db, search_similar_songs


def test_build_vector_collection_creates_embeddings():
	songs = load_songs()[:5]
	prepared = build_vector_collection(songs=songs, backend="memory")
	assert len(prepared) == 5
	assert all(record["embedding"] for record in prepared)


def test_search_similar_songs_returns_ranked_matches():
	songs = load_songs()[:8]
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=songs, backend="memory")

	results = search_similar_songs("songs about heartbreak and healing", top_k=3)
	assert len(results) == 3
	assert results[0]["similarity"] >= results[-1]["similarity"]


def test_search_similar_songs_respects_filters():
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=load_songs(), backend="memory")

	results = search_similar_songs("healing and reflection", top_k=5, filters={"genre": "R&B"})
	assert results
	assert all("R&B" in result["genre"] for result in results)


def test_expand_genre_facets_includes_broad_aliases():
	genres = expand_genre_facets(["R&B / Neo Soul", "Hip-Hop / Rap"])
	assert "R&B" in genres
	assert "Hip-Hop" in genres


def test_get_related_songs_excludes_source_song():
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=load_songs(), backend="memory")

	related = get_related_songs(1, top_k=3)
	assert related
	assert all(song["id"] != 1 for song in related)


def test_get_related_songs_returns_empty_list_for_missing_song():
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=load_songs(), backend="memory")

	assert get_related_songs(9999, top_k=3) == []


def test_ensure_vector_collection_hydrates_numpy_embeddings_without_falling_back():
	song = load_songs()[0]
	vector_store._STORE_STATE.update(
		{
			"backend": "chroma",
			"collection": _FakeCollection(song),
			"records": {},
			"song_index": {song["id"]: dict(song)},
			"status": "idle",
			"initialized": True,
		}
	)

	records = vector_store.ensure_vector_collection()

	assert records
	assert records[0]["id"] == song["id"]
	assert records[0]["embedding"] == [0.1, 0.2, 0.3]


class _FakeCollection:
	def __init__(self, song: dict):
		self.song = song

	def count(self) -> int:
		return 1

	def get(self, include: list[str] | None = None) -> dict:
		return {
			"ids": [str(self.song["id"])],
			"documents": [self.song["search_text"]],
			"metadatas": [vector_store._build_metadata(self.song)],
			"embeddings": np.array([np.array([0.1, 0.2, 0.3])], dtype=object),
		}
