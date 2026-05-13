# LyricLens AI

LyricLens AI is a semantic music theme explorer built as an AI/NLP portfolio project. The application uses Flask for the web layer, a controlled corpus of copyright-safe song descriptions, spaCy for text preprocessing, Sentence-BERT for embeddings, and a vector search layer for meaning-based retrieval.

## Overview

Users can search for ideas such as heartbreak, healing, confidence, loneliness, or growth without relying on exact lyric keywords. The system prepares song descriptions, themes, moods, genre labels, and era metadata for semantic retrieval and dashboard analytics.

Current implemented areas:

- Flask app shell and routed pages
- controlled corpus with 20 structured song entries
- dark neon music-tech UI
- NLP preprocessing and embedding preparation
- vector search and related-song retrieval
- analytics dashboard payloads and chart rendering
- automated pytest suite

## Features

- Meaning-first search experience through [app.py](app.py)
- Controlled corpus and schema validation in [_corpus/songs.json](_corpus/songs.json) and [data_loader.py](data_loader.py)
- NLP helpers in [nlp_pipeline.py](nlp_pipeline.py)
- Vector store and semantic search in [vector_store.py](vector_store.py) and [search_engine.py](search_engine.py)
- Dashboard analytics in [analytics.py](analytics.py)
- Responsive interface templates in [templates](templates)

## Tech Stack

- Backend: Python, Flask
- NLP: spaCy
- Embeddings: Sentence-BERT via `sentence-transformers`
- Vector store: ChromaDB with in-memory fallback support
- Data: JSON corpus
- Frontend: HTML, CSS, Bootstrap 5, Chart.js
- Testing: pytest

## Screenshots

Screenshot capture and insertion are still pending. The intended screenshot set should include:

- homepage hero and corpus highlight cards
- search page with filters and prompt chips
- semantic results page with similarity cards
- dashboard charts and summary metrics

## Project Structure

```text
lyriclensai/
├── app.py
├── config.py
├── data_loader.py
├── nlp_pipeline.py
├── vector_store.py
├── search_engine.py
├── analytics.py
├── requirements.txt
├── requirements-ai.txt
├── README.md
├── _corpus/
├── templates/
├── static/
├── vector_db/
├── tests/
└── docs/
```

## Python Environments

This project currently uses two environments on this machine:

- `.venv` for the lightweight Flask app setup
- `.venv-314-ai` for the AI stack and full project validation

Use the AI environment for NLP, embeddings, vector search, analytics, and full pytest runs.

Verify the active interpreter with:

```powershell
python -c "import sys; print(sys.executable)"
```

The AI environment should report:

```text
C:\Users\cof\lyriclensai\.venv-314-ai\Scripts\python.exe
```

## Installation

Base environment setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

AI environment setup:

```powershell
python -m venv .venv-314-ai
.\.venv-314-ai\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-ai.txt
python -m spacy download en_core_web_sm
```

## How To Run The App

Recommended command:

```powershell
.\.venv-314-ai\Scripts\python.exe app.py
```

Or with Flask:

```powershell
.\.venv-314-ai\Scripts\python.exe -m flask run
```

## How To Run Tests

Run the full suite:

```powershell
.\.venv-314-ai\Scripts\python.exe -m pytest
```

Run targeted slices:

```powershell
.\.venv-314-ai\Scripts\python.exe -m pytest tests/test_nlp_pipeline.py
.\.venv-314-ai\Scripts\python.exe -m pytest tests/test_vector_store.py tests/test_search_engine.py
.\.venv-314-ai\Scripts\python.exe -m pytest tests/test_analytics.py tests/test_routes.py
```

## Embeddings And Search

The search pipeline prepares each song record by combining title, artist, genre, era, themes, moods, summary, and safe excerpt into searchable text. Sentence-BERT embeddings are then generated through the shared model interface in [nlp_pipeline.py](nlp_pipeline.py), and the vector search layer ranks matches through [vector_store.py](vector_store.py) and [search_engine.py](search_engine.py).

## spaCy And BERT Usage

- spaCy is used for text normalization and keyword extraction where the model is available
- Sentence-BERT is used for dense semantic embeddings through the `all-MiniLM-L6-v2` model
- the app retains fallback behavior so modules can still import safely even when a heavyweight ML dependency is unavailable

## Copyright-Safe Corpus Approach

The project avoids full copyrighted lyrics. The corpus uses:

- original summaries
- themes and moods
- short safe excerpts
- structured metadata fields

See [_corpus/corpus_notes.md](_corpus/corpus_notes.md) and [_corpus/source_rules.md](_corpus/source_rules.md) for the governing rules.

## Current Status

Completed through Sprint 8:

- project scaffold and Flask routes
- corpus creation and validation
- UI/UX build
- NLP pipeline
- vector search
- real search/result wiring
- analytics module
- automated testing

Remaining major areas:

- QA documentation refinement
- final project specs polish
- final chatbot integration plan usage in later sprint

## Future Chatbot Integration

The chatbot remains intentionally deferred until the rest of the application is stable. See [docs/chatbot-integration-plan.md](docs/chatbot-integration-plan.md).

## Author

LyricLens AI is being built as an IS421 final project and portfolio-ready AI/NLP demo application.
