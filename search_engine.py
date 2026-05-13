from __future__ import annotations

from data_loader import load_songs
from nlp_pipeline import clean_text, extract_keywords
from vector_store import search_similar_songs


def semantic_search(query: str, filters: dict | None = None, top_k: int = 5) -> list[dict]:
	normalized_query = clean_text(query)
	if not normalized_query:
		return []

	if _is_direct_mood_browse(normalized_query, filters or {}):
		return _build_direct_mood_results(normalized_query, filters or {}, top_k=top_k)

	results = search_similar_songs(normalized_query, top_k=top_k, filters=filters)
	return format_search_results(results, query=normalized_query)


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
	matched_terms = []
	for keyword in query_keywords:
		if keyword in result.get("prepared_text", ""):
			matched_terms.append(keyword)

	if matched_terms:
		preview = ", ".join(matched_terms[:3])
		return f"Semantic match reinforced by prepared text overlap with {preview}."

	theme_preview = ", ".join(result.get("themes", [])[:2])
	mood_preview = ", ".join(result.get("moods", [])[:2])
	return f"Semantic match driven by the song's themes ({theme_preview}) and moods ({mood_preview})."


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
