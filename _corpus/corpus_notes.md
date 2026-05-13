# Corpus Notes

LyricLens AI uses this folder as the source of truth for search content.

## What The Corpus Contains

The current Sprint 2 dataset is a controlled sample corpus of fictional songs created for application development, interface demos, and future semantic search testing.

Each entry includes:

- a stable numeric id
- title and artist strings
- genre and era labels
- themes and moods arrays
- a short original summary
- an optional short safe excerpt
- a combined search_text field

## Why Full Lyrics Are Not Included

Full copyrighted lyrics are intentionally excluded. LyricLens AI is designed to search over structured thematic descriptions rather than reproducing protected song text.

## How Songs Are Represented

Each song record is a compact semantic profile. The summary explains the emotional arc of the song, while themes and moods provide consistent tags that can be counted, filtered, and embedded later.

## How Themes And Moods Support Semantic Search

Themes capture core concepts such as heartbreak, ambition, grief, or confidence. Moods capture the emotional tone such as hopeful, tense, cozy, or cathartic. Combined with genre, era, and summary text, these fields create a reliable search surface for NLP preprocessing and vector similarity in later sprints.
