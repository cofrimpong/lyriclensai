from __future__ import annotations

import logging
import re
from functools import lru_cache
from threading import Lock


DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
FALLBACK_STOP_WORDS = {
	"a",
	"an",
	"and",
	"are",
	"as",
	"at",
	"be",
	"by",
	"for",
	"from",
	"how",
	"in",
	"into",
	"is",
	"it",
	"of",
	"on",
	"or",
	"that",
	"the",
	"their",
	"this",
	"to",
	"with",
}

FALLBACK_TOKEN_PATTERN = re.compile(r"[a-z0-9&'-]+")
LOGGER = logging.getLogger(__name__)
_EMBEDDING_MODEL_CACHE: dict[str, object | None] = {}
_EMBEDDING_MODEL_LOCK = Lock()


def _normalize_basic_text(text: str) -> str:
	text = (text or "").lower().strip()
	text = re.sub(r"\s+", " ", text)
	text = re.sub(r"[^a-z0-9&'\-\s]", " ", text)
	return re.sub(r"\s+", " ", text).strip()


def _fallback_tokens(text: str, remove_stop_words: bool = False) -> list[str]:
	normalized = _normalize_basic_text(text)
	if not normalized:
		return []

	tokens = FALLBACK_TOKEN_PATTERN.findall(normalized)
	if not remove_stop_words:
		return tokens

	return [token for token in tokens if token not in FALLBACK_STOP_WORDS]


def clean_text(text: str, remove_stop_words: bool = False) -> str:
	"""Normalize text for search preparation and embedding input."""
	return " ".join(_fallback_tokens(text, remove_stop_words=remove_stop_words))


@lru_cache(maxsize=1)
def load_spacy_model():
	"""Load spaCy lazily when available, but allow the app to run without it."""
	try:
		import spacy
	except ImportError:
		return None

	for model_name in ("en_core_web_sm", "en_core_web_md"):
		try:
			return spacy.load(model_name)
		except OSError:
			continue
	return None


def extract_keywords(text: str, limit: int = 8) -> list[str]:
	"""Extract useful keywords or noun phrases for search hints and diagnostics."""
	cleaned = clean_text(text)
	if not cleaned:
		return []

	nlp = load_spacy_model()
	if nlp is not None:
		doc = nlp(cleaned)
		keywords: list[str] = []

		for chunk in doc.noun_chunks:
			phrase = clean_text(chunk.text, remove_stop_words=True)
			if phrase and phrase not in keywords:
				keywords.append(phrase)

		for token in doc:
			if token.is_stop or token.is_punct or token.like_num:
				continue
			if token.pos_ not in {"NOUN", "PROPN", "ADJ", "VERB"}:
				continue

			keyword = token.lemma_.strip().lower()
			if keyword and keyword not in keywords:
				keywords.append(keyword)

		return keywords[:limit]

	tokens = []
	for token in _fallback_tokens(text, remove_stop_words=True):
		if token in FALLBACK_STOP_WORDS or len(token) < 4:
			continue
		if token not in tokens:
			tokens.append(token)
	return tokens[:limit]


def prepare_song_text(song: dict, include_keywords: bool = True) -> str:
	"""Combine the structured corpus fields into the main searchable text."""
	segments = [
		song.get("lyric_moment", ""),
		song.get("lyric_lens", ""),
		song.get("lyric_moment", ""),
		song.get("lyric_lens", ""),
		song.get("title", ""),
		song.get("artist", ""),
		song.get("genre", ""),
		song.get("era", ""),
		" ".join(song.get("themes", [])),
		" ".join(song.get("moods", [])),
		" ".join(song.get("themes", [])),
		" ".join(song.get("moods", [])),
		song.get("summary", ""),
		song.get("safe_excerpt", ""),
	]
	base_text = clean_text(" ".join(segment for segment in segments if segment))

	if not include_keywords:
		return base_text

	keywords = extract_keywords(base_text)
	if not keywords:
		return base_text
	return clean_text(f"{base_text} {' '.join(keywords)}")


def load_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL):
	"""Load Sentence-BERT lazily when a compatible runtime is available."""
	if model_name in _EMBEDDING_MODEL_CACHE:
		return _EMBEDDING_MODEL_CACHE[model_name]

	with _EMBEDDING_MODEL_LOCK:
		if model_name in _EMBEDDING_MODEL_CACHE:
			return _EMBEDDING_MODEL_CACHE[model_name]

		LOGGER.info("Loading SentenceTransformer model '%s'.", model_name)
		try:
			from sentence_transformers import SentenceTransformer
		except ImportError:
			LOGGER.warning("sentence-transformers is unavailable; using fallback embeddings.")
			_EMBEDDING_MODEL_CACHE[model_name] = None
			return None

		try:
			model = SentenceTransformer(model_name)
			LOGGER.info("Loaded SentenceTransformer model '%s'.", model_name)
		except Exception:
			LOGGER.exception("Failed to load SentenceTransformer model '%s'; using fallback embeddings.", model_name)
			model = None

		_EMBEDDING_MODEL_CACHE[model_name] = model
		return model


def generate_embedding(text: str, model_name: str = DEFAULT_EMBEDDING_MODEL) -> list[float]:
	"""Generate a dense embedding, falling back to a deterministic vector when unavailable."""
	normalized = clean_text(text)
	model = load_embedding_model(model_name)
	if model is not None:
		vector = model.encode(normalized or "empty", normalize_embeddings=True)
		return [float(value) for value in vector.tolist()]

	return build_fallback_embedding(normalized)


def build_fallback_embedding(text: str, dimensions: int = 12) -> list[float]:
	"""Small deterministic fallback so tests and local prep can run without ML wheels."""
	values = [0.0] * dimensions
	if not text:
		return values

	for index, char in enumerate(text.encode("utf-8")):
		values[index % dimensions] += char / 255.0

	scale = max(sum(values), 1.0)
	return [round(value / scale, 6) for value in values]


def prepare_corpus_embeddings(songs: list[dict], model_name: str = DEFAULT_EMBEDDING_MODEL) -> list[dict]:
	"""Prepare per-song searchable text and embeddings for later vector storage."""
	prepared_records = []

	for song in songs:
		prepared_text = prepare_song_text(song)
		prepared_records.append(
			{
				**song,
				"prepared_text": prepared_text,
				"keywords": extract_keywords(prepared_text),
				"embedding": generate_embedding(prepared_text, model_name=model_name),
			}
		)

	return prepared_records
