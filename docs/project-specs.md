# Project Specs

## Project Title

LyricLens AI

## Project Description

LyricLens AI is a semantic music discovery application that helps users search songs by meaning, mood, and theme rather than exact lyric text. The system uses a controlled, copyright-safe corpus of song descriptions and prepares that content for semantic retrieval through NLP preprocessing and embeddings.

## Problem Statement

Traditional song search depends heavily on exact words, titles, or memorized lyrics. That approach breaks down when a user only knows the emotional idea they want, such as healing after heartbreak or songs about pressure and loneliness. LyricLens AI addresses that gap by letting users search for emotional and thematic meaning instead of literal text matches.

## Target Users

- listeners who want mood-based discovery
- students and recruiters reviewing an AI/NLP portfolio project
- users exploring music through themes, emotions, and semantic similarity

## Main Features

- homepage introducing semantic search for music
- search page with natural-language query input and filters
- semantic results page with similarity scores and explanations
- song detail page with related-song retrieval
- dashboard page with genre, mood, theme, era, and theme-pair analytics
- about page describing the architecture and roadmap

## Functional Requirements

- users can access homepage, search, results, dashboard, about, and song detail routes
- the corpus loads from a controlled JSON source
- each corpus entry includes consistent schema fields
- the NLP pipeline cleans text and extracts keywords
- song records are prepared into searchable text and embeddings
- the vector layer returns similar songs for a user query
- related songs can be retrieved for a selected song
- the dashboard exposes JSON-friendly chart payloads
- pytest coverage exists across routes, corpus, NLP, search, vector, and analytics slices

## Non-Functional Requirements

- UI should feel polished and portfolio-ready
- content must remain copyright-safe
- data must stay structured and predictable
- routes must render cleanly in a local development environment
- tests should run from the AI virtual environment
- code should remain modular enough for future chatbot integration

## Data Schema

Each song record includes:

- `id`
- `title`
- `artist`
- `genre`
- `era`
- `themes`
- `moods`
- `summary`
- `safe_excerpt`
- `search_text`

## NLP Pipeline

The NLP pipeline lives in [nlp_pipeline.py](../nlp_pipeline.py) and provides:

- `clean_text(text)` for normalization
- `extract_keywords(text)` for keyword or noun-phrase extraction
- `prepare_song_text(song)` for combined semantic text preparation
- `prepare_corpus_embeddings(songs)` for prepared corpus records

## Embedding Pipeline

The embedding pipeline uses Sentence-BERT through the `all-MiniLM-L6-v2` interface. Each prepared song record receives an embedding that is later consumed by the vector search layer. A deterministic fallback embedding path also exists so the code can still run in lighter environments.

## Vector Database Design

The vector search layer lives in [vector_store.py](../vector_store.py). It supports:

- collection initialization
- corpus embedding ingestion
- top-k similarity search
- related-song retrieval

ChromaDB is the preferred backend, with an in-memory fallback kept in place so the app remains resilient when a heavier backend is unavailable.

## Search Flow

1. User enters a natural-language query.
2. Query text is normalized.
3. The query is embedded through the same model interface as the corpus.
4. Stored song vectors are ranked by similarity.
5. Results are formatted with percentages, labels, and explanations.
6. The UI renders result cards and allows navigation to song detail pages.

## User Stories

- As a user, I want to search songs by mood so I can find music that matches how I feel.
- As a user, I want similarity scores so I can understand why songs were recommended.
- As a student developer, I want a controlled corpus so the system does not hallucinate song information.
- As a user, I want dashboard analytics so I can explore patterns across genres, moods, and themes.

## Testing Strategy

The test suite is organized by behavior area:

- route tests
- corpus validation tests
- NLP pipeline tests
- vector store tests
- search engine tests
- analytics tests

The intended command is:

```powershell
.\.venv-314-ai\Scripts\python.exe -m pytest
```

## Limitations

- the corpus is controlled and intentionally small
- the dataset uses fictional song entries rather than real licensed lyrical content
- no production deployment layer is configured yet
- Chroma currently emits a non-blocking telemetry deprecation warning during tests
- chatbot integration is intentionally deferred until the rest of the application is finalized
