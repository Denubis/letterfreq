# Personae

User types, their goals, access patterns, and constraints.

## Maintainer

**Role:** Project owner. Operates the corpus-generation, frequency-analysis, and site-build pipelines; edits configuration; reviews and merges changes.

**Goals:**
- Keep the published site current with intended content and corpus.
- Add new analyses (e.g., new word-length pages) without breaking existing ones.
- Maintain reproducibility: re-running scripts on unchanged inputs produces unchanged outputs.

**Access patterns:**
- Local: shell sessions running `uv run python main.py`, `uv run python main_ten.py`, `uv run zensical serve` for preview, `uv run zensical build --clean` for production output, `uv run pytest` for verification.
- Remote: pushes to `main` branch trigger `.github/workflows/docs.yml`, which builds and publishes to GitHub Pages.
- Periodic, event-driven: not a daily flow; triggered by feature work or upstream corpus updates.

**Constraints:**
- Single maintainer assumed; no multi-user coordination required.
- Corpus regeneration is manual and explicit — no scheduled jobs pull upstream changes.

**Key scenarios:**
1. Adding a new analysis page: brainstorm → design plan → implementation plan → execute → verify locally → push.
2. Updating the upstream corpus: run `scripts/build_corpora.py` → review diffs to `data/*.txt` → re-run all `main*.py` scripts → commit.
3. Investigating a bug in the published site: pull, reproduce locally with `zensical serve`, fix, verify, push.

---

## Site visitor

**Role:** Anonymous reader of the published site. No account, no authentication, no server-side state.

**Goals:**
- Look up a specific letter, bigram, or trigram frequency.
- Explore drill-downs (which letters precede/follow a given letter at a given position).
- (Ten-letter page) Find ten-letter words that exercise common letters, bigrams, or word-boundary trigrams.

**Access patterns:**
- HTTP GET for static HTML/CSS/JS/JSON over GitHub Pages.
- Browser-side interaction: click column headers to sort; click bigram/trigram cells to expand drill-down panels.
- Read-only — visitor cannot modify any state.

**Constraints:**
- No personal data collected. No analytics integration (none configured).
- Site degrades gracefully without JavaScript: tables render, but sorting and drill-downs become inert.
- Site must be usable on common modern browsers (Chrome, Firefox, Safari) at desktop and mobile widths.

**Key scenarios:**
1. Visitor lands on `/`, follows a link to `/five/`, scrolls to the bigram heatmap, clicks a cell to see neighbour distributions.
2. Visitor lands on `/ten/`, sorts the letter-coverage ranking by score, scans the transparency column to see which words use which letter sets.
3. Visitor with a slow connection loads `/five/`: tables and CSS render before the JSON-fetched drill-downs become interactive (`navigation.instant.prefetch` is enabled).

---

## Persona Relationships

Maintainer and site visitor never interact directly. The only shared resource is the published site itself: the maintainer writes it, the visitor reads it. There is no contention or authority gradient between them.
