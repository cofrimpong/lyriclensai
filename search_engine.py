from __future__ import annotations

import logging

from data_loader import load_songs
from nlp_pipeline import clean_text, extract_keywords
from vector_store import search_similar_songs


MIN_RELEVANCE_SCORE = 0.28
RELATIVE_RELEVANCE_RATIO = 0.6
LOW_CONFIDENCE_RATIO = 0.92
LOGGER = logging.getLogger(__name__)


def semantic_search(query: str, filters: dict | None = None, top_k: int = 5) -> list[dict]:
	normalized_query = clean_text(query)
	if not normalized_query:
		return []

	if _is_direct_mood_browse(normalized_query, filters or {}):
		return _build_direct_mood_results(normalized_query, filters or {}, top_k=top_k)

	if _is_direct_library_browse(normalized_query, filters or {}):
		return _build_direct_library_results(normalized_query, filters or {}, top_k=top_k)

	try:
		results = search_similar_songs(normalized_query, top_k=top_k, filters=filters)
	except Exception:
		LOGGER.exception("AI search failed for query '%s'; using backup lexical search.", normalized_query)
		results = _build_fast_fallback_results(normalized_query, filters or {}, top_k=top_k)
	filtered_results = _filter_relevant_results(results)
	return format_search_results(filtered_results, query=normalized_query)


def format_search_results(results: list[dict], query: str = "") -> list[dict]:
	query_keywords = extract_keywords(query) if query else []
	formatted_results = []

	for result in results:
		percentage = max(0, min(100, round(result["similarity"] * 100)))
		formatted_results.append(
			{
				**result,
				"similarity_percentage": percentage,
				"match_label": get_match_label(percentage),
				"explanation": build_match_explanation(result, query_keywords),
			}
		)

	return formatted_results


def get_match_label(score: int) -> str:
	if score >= 85:
		return "Very Strong Match"
	if score >= 70:
		return "Strong Match"
	if score >= 55:
		return "Related Match"
	return "Weak Match"


def build_match_explanation(result: dict, query_keywords: list[str]) -> str:
	lyric_fields = " ".join([result.get("lyric_moment", ""), result.get("lyric_lens", "")]).lower()
	matched_terms = []
	for keyword in query_keywords:
		if keyword in lyric_fields:
			matched_terms.append(keyword)
			continue
		if keyword in result.get("prepared_text", ""):
			matched_terms.append(keyword)

	if matched_terms:
		preview = ", ".join(matched_terms[:3])
		return f"Lyric Lens picked up emotional overlap around {preview} in the lyric moment and interpretation."

	if result.get("lyric_lens"):
		return result["lyric_lens"]

	theme_preview = ", ".join(result.get("themes", [])[:2])
	mood_preview = ", ".join(result.get("moods", [])[:2])
	return f"This song resonates through themes like {theme_preview} and moods such as {mood_preview}."


def _is_direct_mood_browse(normalized_query: str, filters: dict) -> bool:
	mood = clean_text(filters.get("mood", ""))
	if not mood or normalized_query != mood:
		return False
	return not any(filters.get(key, "").strip() for key in ["genre", "era", "artist"])


def _build_direct_mood_results(normalized_query: str, filters: dict, top_k: int) -> list[dict]:
	mood = clean_text(filters.get("mood", ""))
	matching_songs = []
	for song in load_songs():
		normalized_moods = [clean_text(item) for item in song.get("moods", [])]
		if mood not in normalized_moods:
			continue
		matching_songs.append(
			{
				**song,
				"similarity": 1.0,
				"similarity_percentage": 100,
				"match_label": "Mood Match",
				"explanation": f"Direct mood browse for {normalized_query} surfaced this song.",
			}
		)

	matching_songs.sort(key=lambda item: (item["artist"], item["title"]))
	return matching_songs[:top_k]


def _is_direct_library_browse(normalized_query: str, filters: dict) -> bool:
	if any(filters.get(key, "").strip() for key in ["genre", "mood", "era", "artist"]):
		return False

	tokens = normalized_query.split()
	if not tokens or len(tokens) > 2:
		return False

	for song in load_songs():
		searchable_values = [
			clean_text(song.get("title", "")),
			clean_text(song.get("artist", "")),
			clean_text(song.get("genre", "")),
			clean_text(song.get("era", "")),
		]
		searchable_values.extend(clean_text(item) for item in song.get("moods", []))
		searchable_values.extend(clean_text(item) for item in song.get("themes", []))
		if normalized_query in searchable_values:
			return True

	return False


def _build_direct_library_results(normalized_query: str, filters: dict, top_k: int) -> list[dict]:
	matching_songs = []
	for song in load_songs():
		if not _song_matches_filters(song, filters):
			continue

		searchable_values = {
			clean_text(song.get("title", "")),
			clean_text(song.get("artist", "")),
			clean_text(song.get("genre", "")),
			clean_text(song.get("era", "")),
		}
		searchable_values.update(clean_text(item) for item in song.get("moods", []))
		searchable_values.update(clean_text(item) for item in song.get("themes", []))
		if normalized_query not in searchable_values:
			continue

		matching_songs.append(
			{
				**song,
				"similarity": 1.0,
				"similarity_percentage": 100,
				"match_label": "Library Match",
				"explanation": f"Direct LyricLens browse for {normalized_query} surfaced this song from the current library.",
			}
		)

	matching_songs.sort(key=lambda item: (item["artist"], item["title"]))
	return matching_songs[:top_k]


def _filter_relevant_results(results: list[dict]) -> list[dict]:
	if not results:
		return []

	top_similarity = results[0]["similarity"]
	if top_similarity >= MIN_RELEVANCE_SCORE:
		minimum_similarity = max(MIN_RELEVANCE_SCORE, top_similarity * RELATIVE_RELEVANCE_RATIO)
	else:
		minimum_similarity = top_similarity * LOW_CONFIDENCE_RATIO

	filtered_results = [result for result in results if result["similarity"] >= minimum_similarity]
	return filtered_results or results[:1]


def _build_fast_fallback_results(query: str, filters: dict, top_k: int) -> list[dict]:
	query_keywords = extract_keywords(query) or query.split()
	ranked_results = []

	for song in load_songs():
		if not _song_matches_filters(song, filters):
			continue

		prepared_text = clean_text(
			" ".join(
				[
					song.get("lyric_moment", ""),
					song.get("lyric_lens", ""),
					" ".join(song.get("themes", [])),
					" ".join(song.get("moods", [])),
					song.get("title", ""),
					song.get("artist", ""),
					song.get("genre", ""),
					song.get("era", ""),
					song.get("summary", ""),
				]
			)
		)

		score = 0.0
		if query and query in prepared_text:
			score += 3.0

		for keyword in query_keywords:
			if keyword and keyword in prepared_text:
				score += 1.0

		if score <= 0:
			continue

		ranked_results.append(
			{
				**song,
				"prepared_text": prepared_text,
				"similarity": min(0.95, 0.24 + score * 0.06),
			}
		)

	ranked_results.sort(key=lambda item: item["similarity"], reverse=True)
	return ranked_results[:top_k]


def _song_matches_filters(song: dict, filters: dict) -> bool:
	genre = filters.get("genre", "").strip()
	mood = filters.get("mood", "").strip()
	era = filters.get("era", "").strip()
	artist = filters.get("artist", "").strip()

	if genre and genre.casefold() not in song.get("genre", "").casefold():
		return False
	if mood and mood not in song.get("moods", []):
		return False
	if era and era != song.get("era"):
		return False
	if artist and artist != song.get("artist"):
		return False
	return True
