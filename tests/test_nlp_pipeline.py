from data_loader import load_songs
from nlp_pipeline import build_fallback_embedding, clean_text, extract_keywords, prepare_corpus_embeddings, prepare_song_text


def test_clean_text_lowercases_and_compacts_spaces():
	cleaned = clean_text("  Songs   About HEARTBREAK   and Healing  ")
	assert cleaned == "songs about heartbreak and healing"


def test_clean_text_optionally_removes_stop_words():
	cleaned = clean_text("songs about the pain and the healing", remove_stop_words=True)
	assert "the" not in cleaned.split()
	assert "healing" in cleaned


def test_extract_keywords_returns_useful_tokens_without_spacy():
	keywords = extract_keywords("songs about confidence, self-worth, and healing after pressure")
	assert "confidence" in keywords
	assert "healing" in keywords


def test_extract_keywords_falls_back_cleanly_when_spacy_is_unavailable(monkeypatch):
	monkeypatch.setattr("nlp_pipeline.load_spacy_model", lambda: None)
	keywords = extract_keywords("songs about confidence, self-worth, and healing after pressure")
	assert "confidence" in keywords
	assert "self-worth" in keywords


def test_prepare_song_text_combines_expected_fields():
	song = load_songs()[0]
	prepared = prepare_song_text(song, include_keywords=False)
	assert song["title"].lower() in prepared
	assert song["artist"].lower() in prepared
	assert clean_text(song["genre"]) in prepared
	assert " ".join(song["themes"]).split()[0].lower() in prepared


def test_fallback_embedding_is_deterministic():
	first = build_fallback_embedding("heartbreak healing growth")
	second = build_fallback_embedding("heartbreak healing growth")
	assert first == second
	assert len(first) == 12


def test_prepare_corpus_embeddings_enriches_records():
	songs = load_songs()[:3]
	prepared = prepare_corpus_embeddings(songs)
	assert len(prepared) == 3
	assert all(record["prepared_text"] for record in prepared)
	assert all(isinstance(record["keywords"], list) for record in prepared)
	assert all(isinstance(record["embedding"], list) for record in prepared)
	assert all(len(record["embedding"]) > 0 for record in prepared)
