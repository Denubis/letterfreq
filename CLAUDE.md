# letterfreq

Positional letter frequency analysis for five-letter English words, published as a static site.

## Stack

- **Python 3.14** with **uv** for package management
- **Zensical** (v0.0.28) for static site generation — successor to mkdocs-material by squidfunk
- **GitHub Pages** for hosting via `.github/workflows/docs.yml`

## Project structure

```
docs/           — Markdown source for the site (Zensical reads this)
main.py         — Python script to generate frequency data
zensical.toml   — Zensical configuration (TOML, not mkdocs.yml)
site/           — Build output (gitignored)
```

## Commands

```bash
uv run zensical serve     # Local preview at http://localhost:8000
uv run zensical build     # Build static site to site/
uv run python main.py     # Generate frequency data
```

## Content concept

Inspired by Norvig's Mayzner revisited (https://norvig.com/mayzner.html).
Analysis of 5-letter words with:
- Unigram frequencies by position (1-5)
- Bigram frequencies by position, forward and backward looking (grid format)
- Trigram frequencies by position, high-frequency entries

Freshness: 2026-03-22
