# Project Glossary

Ubiquitous language for letterfreq. Every term here means the same thing in code, docs, and conversation.

## Domain Terms

- **Baseline corpus**: The set of 3–10 letter words derived from dwyl/english-words. Used to compute reference letter and bigram rates that weight ten-letter word scoring. The trigram baseline is the same corpus filtered further to length ≥ 4 (see DR3 in the ten-letter design plan).
- **Bigram**: A consecutive two-letter sequence within a word (e.g. `ca`, `at` in `cat`). Counted as a sliding window across each word; serves as both a reference frequency table and a scoring dimension.
- **Trigram**: A consecutive three-letter sequence. In the five-letter site this means positional gap-fill trigrams (3 gap positions × 3 word windows). In the ten-letter site this means *only* the start trigram (positions 1–3) and end trigram (positions n−2, n−1, n) of each word.
- **Drill-down**: A browser-side panel that appears below a bigram or trigram cell when clicked, showing the neighbour-frequency distribution for the selected letter pair. Implemented in `sort-tables.js` and `trigram-expand.js`.
- **Heatmap**: A 26×26 (or 26×N) coloured grid where each cell's background intensity reflects its count, normalised per column.
- **Per-column normalisation**: Grid colour scale computed independently for each column, so the densest letter in column 1 appears as fully saturated as the densest letter in column 26 — used because raw counts vary by orders of magnitude across positions.
- **Letter-coverage score**: A per-word score for ten-letter words equal to the sum of baseline letter rates for each *distinct* letter in the word. Repeated letters do not increase the score (hard cap).
- **Bigram score** (ten-letter): Sum of baseline bigram rates over the 9 consecutive bigram positions in a ten-letter word, including duplicates.
- **Trigram score** (ten-letter): Sum of the start-trigram baseline rate and the end-trigram baseline rate for a ten-letter word.
- **Positional endpoint score** (ten-letter): A per-word score for ten-letter words equal to `f_first(w[0]) + f_last(w[-1])`, where `f_first` and `f_last` are the rates of each letter appearing as the first or last letter of any baseline word respectively. Both terms contribute even when `w[0] == w[-1]` (no distinct cap, distinguishing this score from `letter_score`). See DR8 in the ten-letter design plan.
- **First-letter frequency / last-letter frequency**: Per-letter counts (and rates) over the baseline corpus, where each baseline word contributes exactly one count to first-letter (its `word[0]`) and one count to last-letter (its `word[-1]`). No minimum-length filter — every baseline word contributes regardless of length. Used as the weights for `positional_endpoint_score`.
- **Transparency column**: A table column in the ten-letter ranking tables that shows the specific letters, bigrams, or trigrams that drove a word's score. Makes the rankings auditable.
- **Per-occurrence rate**: A frequency expressed as `count / total-occurrences-of-this-kind` (not `count / total-words`). Used as the baseline weight when scoring.
- **Positional unigram / positional bigram / positional trigram**: In the five-letter analysis, frequencies counted at specific positions within a five-letter word (e.g., letter `s` at position 1; bigram `th` at positions 1–2). Differs from the ten-letter site, which uses position-independent counts for the baseline.

## Technical Terms

- **dwyl/english-words**: Open-source word list (~370k English words, Unlicense) hosted at `github.com/dwyl/english-words`. Raw upstream source for all committed corpus files.
- **Zensical**: Static site generator (>= 0.0.33), successor to mkdocs-material. Configured via `zensical.toml`. Reads `docs/`, writes `site/`.
- **Polars**: Python DataFrame library used for frequency computation in the existing `main.py`. The new `letterfreq/` package uses plain dicts for clarity.
- **FCIS / functional core, imperative shell**: An architectural pattern separating pure functions (no I/O, no side effects; easy to test) from the imperative code that reads files, calls those functions, and writes output. Applied in this project via the `letterfreq/` package split.
- **GitHub Pages**: Static-site hosting target; deployment triggered by `.github/workflows/docs.yml`.

## Abbreviations

| Abbreviation | Full Form | Context |
|-------------|-----------|---------|
| AC | Acceptance Criterion | Design plan acceptance criteria, scoped per design (e.g. `ten-letter-page.AC1.1`). |
| DFD | Data-Flow Diagram | This `dfd/` directory. |
| DR | Decision Record | Design plan ADR-style decision entries. |
| DoD | Definition of Done | Design plan section listing what "done" means. |
| FCIS | Functional Core, Imperative Shell | See above. |

## Deprecated Terms

| Old Term | Replaced By | Since | Reason |
|----------|-------------|-------|--------|
| (none) | | | |
