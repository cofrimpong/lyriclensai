# QA Report

## QA Scope

This report covers the locally implemented LyricLens AI application through Sprint 9 documentation work.

## Automated QA Status

Full automated test command:

```powershell
.\.venv-314-ai\Scripts\python.exe -m pytest
```

Latest recorded result:

- 32 tests passed
- 1 non-blocking warning from Chroma telemetry

## Manual QA Checklist

- Home page loads
- Search page loads
- Dashboard page loads
- About page loads
- Song detail page loads
- Navbar links work
- Search form submits and redirects to results
- Semantic result cards render
- Similarity percentages render
- Dashboard charts render from JSON payloads
- Mobile layout remains usable
- No missing static files observed during local runs
- No full lyrics are displayed
- Corpus rules are followed by the current dataset

## Browser Testing

Recommended browser validation targets:

- Chrome
- Microsoft Edge

## Responsive Testing Targets

- desktop
- tablet
- mobile

## Accessibility Checks

- verify readable contrast on dark neon surfaces
- verify visible focus states for navigation and form controls
- verify form labels remain associated with inputs
- verify keyboard navigation on navbar and search interface

## Known Warnings And Notes

- Chroma emits a deprecation warning tied to future Python 3.16 behavior during route tests
- Hugging Face may emit an unauthenticated request warning when the embedding model downloads for the first time
- Windows may show a symlink-related cache warning from `huggingface_hub`; this does not block model usage

## Open Manual QA Items

- capture final screenshots for README
- perform explicit browser-by-browser responsive walkthroughs
- perform a browser console review after a fresh app run
- verify mobile spacing visually after final documentation sprint closes
