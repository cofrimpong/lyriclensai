from __future__ import annotations

from math import sqrt
from pathlib import Path
from threading import Lock

from data_loader import load_songs
from nlp_pipeline import DEFAULT_EMBEDDING_MODEL, clean_text, generate_embedding, prepare_corpus_embeddings


DEFAULT_COLLECTION_NAME = "lyriclens_songs"
DEFAULT_PERSIST_DIRECTORY = Path(__file__).resolve().parent / "vector_db" / "chroma"

_STORE_STATE = {
	"backend": "memory",
	"collection_name": DEFAULT_COLLECTION_NAME,
	"persist_directory": DEFAULT_PERSIST_DIRECTORY,
	"client": None,
	"collection": None,
	"records": {},
	"status": "idle",
}

_STORE_LOCK = Lock()


def initialize_vector_db(
	persist_directory: str | Path | None = None,
	collection_name: str = DEFAULT_COLLECTION_NAME,
	backend: str = "auto",
) -> dict:
	persist_path = Path(persist_directory) if persist_directory else DEFAULT_PERSIST_DIRECTORY
	persist_path.mkdir(parents=True, exist_ok=True)

	chosen_backend = backend
	client = None
	collection = None

	if backend in {"auto", "chroma"}:
		try:
			import chromadb

			client = chromadb.PersistentClient(path=str(persist_path))
			try:
				client.delete_collection(collection_name)
			except Exception:
				pass
			collection = client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
			chosen_backend = "chroma"
		except Exception:
			if backend == "chroma":
				raise
			chosen_backend = "memory"

	_STORE_STATE.update(
		{
			"backend": chosen_backend,
			"collection_name": collection_name,
			"persist_directory": persist_path,
			"client": client,
			"collection": collection,
			"records": {},
			"status": "idle",
		}
	)
	return _STORE_STATE


def build_vector_collection(
	songs: list[dict] | None = None,
	model_name: str = DEFAULT_EMBEDDING_MODEL,
	backend: str = "auto",
	persist_directory: str | Path | None = None,
) -> list[dict]:
	source_songs = songs if songs is not None else load_songs()
	initialize_vector_db(persist_directory=persist_directory, backend=backend)
	_STORE_STATE["status"] = "building"
	try:
		prepared_records = prepare_corpus_embeddings(source_songs, model_name=model_name)
		add_song_embeddings(prepared_records)
		_STORE_STATE["status"] = "ready"
		return prepared_records
	except Exception:
		_STORE_STATE["status"] = "idle"
		raise


def ensure_vector_collection(
	songs: list[dict] | None = None,
	model_name: str = DEFAULT_EMBEDDING_MODEL,
	backend: str = "auto",
	persist_directory: str | Path | None = None,
) -> list[dict]:
	if _STORE_STATE["records"]:
		return list(_STORE_STATE["records"].values())

	with _STORE_LOCK:
		if _STORE_STATE["records"]:
			return list(_STORE_STATE["records"].values())

		return build_vector_collection(
			songs=songs,
			model_name=model_name,
			backend=backend,
			persist_directory=persist_directory,
		)


def is_vector_collection_ready() -> bool:
	return _STORE_STATE["status"] == "ready" and bool(_STORE_STATE["records"])


def is_vector_collection_building() -> bool:
	return _STORE_STATE["status"] == "building"


def add_song_embeddings(songs: list[dict]) -> None:
	if _STORE_STATE["collection"] is None and _STORE_STATE["backend"] == "memory" and not _STORE_STATE["records"]:
		initialize_vector_db(
			persist_directory=_STORE_STATE["persist_directory"],
			collection_name=_STORE_STATE["collection_name"],
			backend=_STORE_STATE["backend"],
		)

	prepared_records = []
	for song in songs:
		prepared_record = dict(song)
		prepared_record.setdefault("prepared_text", prepared_record.get("search_text") or clean_text(prepared_record["summary"]))
		prepared_record.setdefault("embedding", generate_embedding(prepared_record["prepared_text"]))
		prepared_records.append(prepared_record)
		_STORE_STATE["records"][prepared_record["id"]] = prepared_record

	if _STORE_STATE["backend"] != "chroma" or _STORE_STATE["collection"] is None:
		return

	collection = _STORE_STATE["collection"]
	collection.add(
		ids=[str(song["id"]) for song in prepared_records],
		embeddings=[song["embedding"] for song in prepared_records],
		documents=[song["prepared_text"] for song in prepared_records],
		metadatas=[_build_metadata(song) for song in prepared_records],
	)


def search_similar_songs(query: str, top_k: int = 5, filters: dict | None = None, allow_cold_start: bool = True) -> list[dict]:
	if not _STORE_STATE["records"]:
		if not allow_cold_start:
			return []
		ensure_vector_collection()

	normalized_query = clean_text(query)
	query_embedding = generate_embedding(normalized_query)
	active_filters = filters or {}

	ranked_results = []
	for record in _STORE_STATE["records"].values():
		if not _matches_filters(record, active_filters):
			continue

		similarity = cosine_similarity(query_embedding, record["embedding"])
		ranked_results.append(
			{
				**record,
				"similarity": similarity,
			}
		)

	ranked_results.sort(key=lambda item: item["similarity"], reverse=True)
	return ranked_results[:top_k]


def get_related_songs(song_id: int, top_k: int = 3, allow_cold_start: bool = True) -> list[dict]:
	if not _STORE_STATE["records"]:
		if not allow_cold_start:
			return []
		ensure_vector_collection()

	source_song = _STORE_STATE["records"].get(song_id)
	if source_song is None:
		return []

	ranked_results = []
	for candidate in _STORE_STATE["records"].values():
		if candidate["id"] == song_id:
			continue

		similarity = cosine_similarity(source_song["embedding"], candidate["embedding"])
		ranked_results.append({**candidate, "similarity": similarity})

	ranked_results.sort(key=lambda item: item["similarity"], reverse=True)
	return ranked_results[:top_k]


def cosine_similarity(first: list[float], second: list[float]) -> float:
	numerator = sum(left * right for left, right in zip(first, second))
	first_norm = sqrt(sum(value * value for value in first))
	second_norm = sqrt(sum(value * value for value in second))
	if first_norm == 0 or second_norm == 0:
		return 0.0
	return numerator / (first_norm * second_norm)


def _matches_filters(record: dict, filters: dict) -> bool:
	genre = filters.get("genre")
	era = filters.get("era")
	artist = filters.get("artist")
	mood = filters.get("mood")

	if genre and not _genre_matches(record["genre"], genre):
		return False
	if era and record["era"] != era:
		return False
	if artist and record["artist"] != artist:
		return False
	if mood and mood not in record["moods"]:
		return False
	return True


def expand_genre_facets(genres: list[str]) -> list[str]:
	expanded = set(genres)
	for genre in genres:
		expanded.update(_derive_genre_aliases(genre))
	return sorted(expanded)


def _genre_matches(record_genre: str, requested_genre: str) -> bool:
	normalized_record = clean_text(record_genre)
	normalized_requested = clean_text(requested_genre)
	if not normalized_requested:
		return True
	if normalized_record == normalized_requested:
		return True
	if normalized_requested in normalized_record:
		return True
	return normalized_record in {_normalize_genre_alias(alias) for alias in _derive_genre_aliases(requested_genre)}


def _derive_genre_aliases(genre: str) -> set[str]:
	aliases = set()
	parts = [part.strip() for part in genre.split("/") if part.strip()]
	for part in parts:
		aliases.add(part)
		if "-" in part:
			aliases.add(part.split("-", maxsplit=1)[0].strip())
		if "&" in part:
			aliases.add(part.replace("&", " and ").strip())
	return aliases


def _normalize_genre_alias(value: str) -> str:
	return clean_text(value)


def _build_metadata(song: dict) -> dict:
	return {
		"id": song["id"],
		"title": song["title"],
		"artist": song["artist"],
		"genre": song["genre"],
		"era": song["era"],
		"themes": "|".join(song["themes"]),
		"moods": "|".join(song["moods"]),
		"summary": song["summary"],
	}
