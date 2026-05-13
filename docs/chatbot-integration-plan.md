# Chatbot Integration Plan

## Status

Chatbot work is intentionally deferred until the core search application, analytics, testing, QA, and documentation are finalized.

## Future Integration Goals

- use the same vector database as the search experience
- retrieve relevant corpus records before generating a response
- answer only from retrieved corpus context
- avoid unsupported claims about songs or lyrics
- cite or display retrieved song cards in the chat response

## Proposed Architecture

1. Receive a conversational user prompt.
2. Convert the prompt into an embedding using the same query pipeline.
3. Retrieve the top matching songs from the vector store.
4. Build a grounded response only from those retrieved records.
5. Render supporting song cards, themes, moods, and explanation text alongside the response.

## Safety Requirements

- no full copyrighted lyrics
- no unsupported factual claims about songs
- no answers outside retrieved corpus context
- preserve the same copyright-safe dataset rules used by the main app

## UI Direction

- chat interface should feel consistent with the current dark neon LyricLens AI design
- response area should include cited songs or retrieved context cards
- the chat view should support mood exploration, recommendation follow-ups, and theme comparisons

## Implementation Dependencies

- stable corpus and vector search layer
- finalized search and song-detail behavior
- completed QA and documentation baseline
- clear retrieved-context formatting strategy