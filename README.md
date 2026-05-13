# LyricLens AI

LyricLens AI is an AI-powered emotional music discovery platform that helps users explore songs through moods, lyrical meaning, themes, emotional interpretation, and semantic similarity search.

Instead of searching music only by artist or title, LyricLens AI allows users to discover songs through feelings, experiences, emotional states, and lyrical storytelling. The platform combines natural language processing, embeddings, vector databases, Spotify integration, and interactive UI design to create a modern music exploration experience.

Live Site: https://lyriclensai.onrender.com

---

# Features

## Emotional Music Discovery
Users can search music through:
- emotions
- moods
- themes
- relationship situations
- personal experiences
- lyrical meaning

Examples:
- heartbreak
- healing
- confidence
- self growth
- loneliness
- motivation
- celebration
- emotional vulnerability

---

## Semantic Search with NLP
LyricLens AI uses Natural Language Processing techniques to understand the emotional meaning behind songs instead of relying only on keyword matching.

The system analyzes:
- lyric moments
- emotional interpretation
- moods
- themes
- genres
- artist context

This allows semantically similar songs to be recommended even when exact words are not used in the search query.

---

# AI / NLP Technologies Used

## Sentence Transformers
Sentence Transformers are used to generate semantic embeddings for emotional music search.

## ChromaDB Vector Database
ChromaDB stores vector embeddings for similarity matching and semantic retrieval.

## Spotify API Integration
Spotify Web API integration provides:
- album artwork
- track metadata
- popularity information
- artist links
- Spotify authentication

## Flask Backend
The application backend is built using Flask and handles:
- routing
- search processing
- Spotify OAuth
- semantic recommendation logic
- chatbot interaction
- vector search handling

---

# Core Functionalities

## Semantic Search Engine
Users can search for songs using emotional or descriptive language rather than exact titles.

Examples:
- "songs about healing"
- "music for confidence"
- "feeling emotionally lost"
- "songs about pressure and success"

The application returns semantically related songs using vector similarity search.

---

## Lyric Moments
Each song contains a highlighted lyrical moment that emotionally represents the song.

Example:
> “Still wanna try, still believe in good days.”

These lyric moments help create emotional connection and music storytelling throughout the platform.

---

## Emotional Interpretation
Every song includes a “LyricLens Interpretation” section that explains:
- emotional themes
- lyrical meaning
- emotional atmosphere
- song context

---

## Spotify Connect
Users can connect their Spotify accounts through Spotify OAuth authentication.

Spotify integration supports:
- artist pages
- track links
- album artwork
- external listening experience

---

## Chatbot Interface
LyricLens AI includes a music discovery chatbot that:
- answers from the current LyricLens dataset
- recommends songs based on moods and emotions
- explains lyrical themes
- suggests emotionally similar songs

The chatbot is constrained to the existing music library to reduce hallucinations and improve recommendation quality.

---

# User Experience Design

The platform was designed to feel immersive, emotional, and modern.

UI/UX features include:
- glassmorphism styling
- glowing hover effects
- animated gradients
- rotating lyric hero sections
- emotional discovery carousels
- responsive mobile design
- Spotify-inspired visual elements
- floating musical note animations

The design goal was to create a cinematic emotional music discovery experience.

---

# Dataset Structure

Songs are stored inside:
```text
_corpus/songs.json
````

Each song contains:

* title
* artist
* genre
* era
* moods
* themes
* lyric_moment
* lyric_lens
* Spotify URLs

---

# Project Architecture

```text
Frontend
│
├── HTML / CSS / JavaScript
├── Glassmorphism UI
├── Dynamic search interface
└── Interactive music cards

Backend
│
├── Flask
├── Semantic search logic
├── Spotify OAuth
├── Spotify metadata enrichment
├── Chatbot routing
└── API handling

AI Layer
│
├── Sentence Transformers
├── Embedding generation
├── ChromaDB vector storage
└── Semantic similarity matching
```

---

# Deployment

LyricLens AI is deployed on Render.

Production deployment includes:

* lazy model loading
* persistent ChromaDB handling
* Spotify metadata caching
* memory optimization
* stable vector search architecture

---

# Local Installation

## Clone Repository

```bash
git clone https://github.com/cofrimpong/lyriclensai.git
cd lyriclensai
```

---

## Create Virtual Environment

```bash
python -m venv .venv
```

Activate environment:

### Windows

```bash
.venv\Scripts\activate
```

### Mac/Linux

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=https://lyriclensai.onrender.com/spotify/callback
```

---

# Run Application

```bash
python app.py
```

---

# Testing

Run automated tests:

```bash
pytest
```

Testing includes:

* semantic search
* route handling
* Spotify integration
* chatbot responses
* vector persistence
* UI rendering logic

---

# Future Improvements

Potential future enhancements include:

* playlist generation
* deeper Spotify personalization
* expanded music corpus
* advanced recommendation analytics
* emotion clustering visualizations
* real-time lyric embedding updates
* user mood history tracking

---

# Author

Christabel Frimpong

GitHub:
[https://github.com/cofrimpong](https://github.com/cofrimpong)

---

# License

This project was created for educational, portfolio, and AI/NLP learning purposes.

```
```