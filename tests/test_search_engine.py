import search_engine
from search_engine import format_search_results, get_match_label, semantic_search
from vector_store import build_vector_collection, initialize_vector_db
from data_loader import load_songs


def test_get_match_label_uses_expected_ranges():
	assert get_match_label(90) == "Very Strong Match"
	assert get_match_label(77) == "Strong Match"
	assert get_match_label(60) == "Related Match"
	assert get_match_label(40) == "Weak Match"


def test_format_search_results_adds_frontend_fields():
	formatted = format_search_results(
		[
			{
				"id": 1,
				"title": "Midnight Glass",
				"themes": ["heartbreak", "healing"],
				"moods": ["reflective", "hopeful"],
				"prepared_text": "midnight glass heartbreak healing reflective hopeful",
				"similarity": 0.86,
			}
		],
		query="heartbreak and healing",
	)

	assert formatted[0]["similarity_percentage"] == 86
	assert formatted[0]["match_label"] == "Very Strong Match"
	assert formatted[0]["explanation"]


def test_semantic_search_returns_matches():
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=load_songs(), backend="memory")

	results = semantic_search("songs about heartbreak and healing", top_k=4)
	assert results
	assert len(results) <= 4
	assert all("similarity_percentage" in result for result in results)


def test_semantic_search_returns_empty_list_for_blank_query():
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=load_songs(), backend="memory")

	assert semantic_search("   ", top_k=4) == []


def test_semantic_search_uses_fast_path_for_direct_mood_browse(monkeypatch):
	def fail_if_called(*args, **kwargs):
		raise AssertionError("vector search should not run for direct mood browse")

	monkeypatch.setattr(search_engine, "search_similar_songs", fail_if_called)

	results = semantic_search("emotional", filters={"mood": "emotional"}, top_k=5)
	assert results
	assert all("emotional" in [mood.lower() for mood in result["moods"]] for result in results)


def test_semantic_search_respects_filters():
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=load_songs(), backend="memory")

	results = semantic_search("healing and reflection", filters={"genre": "R&B"}, top_k=5)
	assert results
	assert all("R&B" in result["genre"] for result in results)


def test_semantic_search_uses_lyric_moment_and_lens_language():
	initialize_vector_db(backend="memory")
	build_vector_collection(songs=load_songs(), backend="memory")

	results = semantic_search("lonely at the top pressure of success", top_k=5)
	assert results
	assert results[0]["title"] == "Lonely At The Top"
