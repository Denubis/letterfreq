# Ten-Letter Page Design

**GitHub Issue:** None

## Summary

This work extends the existing single-page letter-frequency site into a three-page site. The current five-letter analysis moves to `/five/`, a new `/ten/` page is added, and a landing page at `/` links both. The ten-letter page answers a different question from the five-letter page: rather than positional heatmaps, it asks which ten-letter words are best covered by the most common letters, bigrams, and trigrams in English. It does this through two halves: reference tables (letter, bigram, start/end trigram frequencies computed over a broad 3–10 letter baseline corpus) and ranking tables (top-50 ten-letter words scored against those baseline rates, with a transparency column showing the components driving each word's score).

The implementation reorganises Python into a small `letterfreq/` package with a strict functional-core/imperative-shell split: pure modules (`reference.py`, `scoring.py`, `render.py`) are independently testable; entry scripts (`main.py`, `main_ten.py`) do I/O and call them. Corpus files are pre-filtered and committed, keeping build times fast. The static-first rendering approach from the five-letter page is preserved: all tables are emitted as HTML embedded in Markdown, with client-side sorting via the existing JS.

## Definition of Done

The design is done when:

1. The site serves three URLs via Zensical: `/` (landing), `/five/` (existing five-letter analysis, behaviour unchanged), `/ten/` (new ten-letter page). All three are reachable from the site navigation.
2. The ten-letter page displays three reference tables computed over the 3–10 letter baseline corpus: (a) letter frequency (26 rows, sortable); (b) top-100 bigram frequency (flat sortable list); (c) two side-by-side top-50 ranked tables for start and end trigrams.
3. The ten-letter page displays three top-50 rankings of ten-letter words, each ranked by one score using baseline per-occurrence rates: letter-coverage (Σ f over distinct letters), bigram (Σ f over 9 consecutive bigrams), start+end trigram. All sortable; each includes a transparency column explaining the word's score.
4. `pyproject.toml` pins `zensical>=0.0.33`; the existing five-letter page renders correctly after the bump; dark/light toggle and instant navigation still work.
5. Two new data files are committed: `data/words_10.txt` (10-letter words) and `data/words_3_to_10.txt` (3–10 letter baseline corpus), each filtered from dwyl/english-words to lowercase a–z only.
6. Scoring functions live in a new `letterfreq/scoring.py` pure module, tested with hand-checked inputs verifying each formula.
7. `CLAUDE.md` is updated to reflect the new multi-page layout, the `letterfreq/` package, the new corpus files, and a fresh freshness date.

## Acceptance Criteria

### ten-letter-page.AC1: Baseline letter and bigram frequencies are correct
- **ten-letter-page.AC1.1 Success:** `letter_counts(["cat", "act"])` returns `{a:2, c:2, t:2}`.
- **ten-letter-page.AC1.2 Success:** `bigram_counts(["cat", "act"])` returns `{ca:1, at:1, ac:1, ct:1}`.
- **ten-letter-page.AC1.3 Success:** `to_rates({a:2, c:2, t:2}, total=6)` returns floats summing to 1.0 with each value 1/3.
- **ten-letter-page.AC1.4 Success:** `letter_counts` and `bigram_counts` on the actual `words_3_to_10.txt` corpus produce non-zero counts for every letter a–z.

### ten-letter-page.AC2: Baseline start/end trigrams are correct
- **ten-letter-page.AC2.1 Success:** `start_trigram_counts(["cation", "static"])` returns `{cat:1, sta:1}`.
- **ten-letter-page.AC2.2 Success:** `end_trigram_counts(["cation", "static"])` returns `{ion:1, tic:1}`.
- **ten-letter-page.AC2.3 Success:** A 4-letter word `"cats"` contributes `{cat:1}` to start trigram counts and `{ats:1}` to end trigram counts — the two are distinct because position 3 ≠ position n−2 when n ≥ 4.
- **ten-letter-page.AC2.4 Success:** A 3-letter word `"cat"` is excluded from both `start_trigram_counts` and `end_trigram_counts` when the default `min_length=4` is in effect.

### ten-letter-page.AC3: Scoring formulas
- **ten-letter-page.AC3.1 Success:** `letter_score("aaaaaaaaaa", {a:0.1, ...})` returns 0.1 (distinct-only cap).
- **ten-letter-page.AC3.2 Success:** `letter_score("abcdefghij", rates)` returns `sum(rates[l] for l in "abcdefghij")`.
- **ten-letter-page.AC3.3 Success:** `bigram_score` on a 10-letter word with controlled rates returns the sum of the 9 consecutive-bigram rates.
- **ten-letter-page.AC3.4 Success:** `trigram_score("abcdefghij", start_rates, end_rates)` returns `start_rates["abc"] + end_rates["hij"]`.

### ten-letter-page.AC4: Ranking ordering and tie-break
- **ten-letter-page.AC4.1 Success:** Two words with identical scores are returned in alphabetical order.
- **ten-letter-page.AC4.2 Success:** `top_n_by_score` returns exactly `n` entries when ≥`n` candidates exist.
- **ten-letter-page.AC4.3 Success:** Rank-1 entry has the highest score among all candidates.

### ten-letter-page.AC5: Reference tables render correctly on /ten/
- **ten-letter-page.AC5.1 Success:** Letter-frequency table has 26 rows.
- **ten-letter-page.AC5.2 Success:** Bigram top-100 table has exactly 100 rows.
- **ten-letter-page.AC5.3 Success:** Start- and end-trigram tables have 50 rows each, side-by-side in wide viewport, stacked in narrow viewport.
- **ten-letter-page.AC5.4 Success:** All three reference tables expose sortable column headers (`<th class="sortable">`) and respond to click-to-sort.

### ten-letter-page.AC6: Ranking tables render correctly on /ten/
- **ten-letter-page.AC6.1 Success:** Letter-coverage ranking table has 50 rows; transparency column lists the distinct letters of each word, sorted by individual letter rate.
- **ten-letter-page.AC6.2 Success:** Bigram ranking table has 50 rows; transparency column lists the 3 bigrams from the word that contribute most to its score, where contribution = bigram_rate × number_of_times_that_bigram_appears_in_the_word. (For a word like `statistics` where `st` appears 3 times in 9 consecutive-bigram positions, `st` is listed once with its full contribution.)
- **ten-letter-page.AC6.3 Success:** Trigram ranking table has 50 rows with separate start-trigram and end-trigram columns.
- **ten-letter-page.AC6.4 Success:** All three ranking tables sortable.

### ten-letter-page.AC7: Site structure preserved after Zensical bump
- **ten-letter-page.AC7.1 Success:** `uv run zensical build --clean` succeeds with `zensical>=0.0.33`.
- **ten-letter-page.AC7.2 Success:** `/five/` renders with bigram drill-downs and trigram expansions still working.
- **ten-letter-page.AC7.3 Success:** `/` shows the landing page with links to `/five/` and `/ten/`.
- **ten-letter-page.AC7.4 Success:** `zensical.toml` `nav` block exposes Home, Five-letter, Ten-letter.
- **ten-letter-page.AC7.5 Success:** Dark/light toggle and `navigation.instant` behave on both pages.

### ten-letter-page.AC8: Corpus file invariants
- **ten-letter-page.AC8.1 Success:** `data/words_10.txt` is non-empty; every line matches `^[a-z]{10}$`.
- **ten-letter-page.AC8.2 Success:** `data/words_3_to_10.txt` is non-empty; every line matches `^[a-z]{3,10}$`.
- **ten-letter-page.AC8.3 Success (invariant):** `data/words.txt` (existing 5-letter) is non-empty, line count is at least 15,000, every line matches `^[a-z]{5}$`. This is a structural invariant that catches accidental modification by this refactor while remaining robust to legitimate future regeneration of the file from upstream.

### ten-letter-page.AC9: Documentation freshness
- **ten-letter-page.AC9.1 Success:** `CLAUDE.md` references `docs/five/`, `docs/ten/`, `letterfreq/` package, `words_10.txt`, `words_3_to_10.txt`.
- **ten-letter-page.AC9.2 Success:** `CLAUDE.md` freshness date is `2026-04-19` or later.

## Glossary

- **Zensical**: Static site generator (v0.0.28+) used to build and serve the documentation site. Successor to mkdocs-material. Configured via `zensical.toml`; outputs to `site/`.
- **dwyl/english-words**: Open-source word list (~370k English words) used as the raw corpus source. Filtered at corpus-generation time to produce the committed word files.
- **baseline corpus**: The set of 3–10 letter words derived from dwyl/english-words, used to compute reference letter/bigram/trigram rates. Rates from this corpus are used as weights when scoring ten-letter words.
- **bigram**: A consecutive two-letter sequence within a word (e.g. `ca`, `at` in `cat`). Used both as a reference frequency table and as a scoring dimension for ten-letter words.
- **trigram**: A consecutive three-letter sequence. In this document, only the first three letters (start trigram) and last three letters (end trigram) of each word are counted, not all interior trigrams. Trigram counts are derived from words of length ≥ 4 (per DR3) so the start and end distributions are cleanly separable.
- **letter-coverage score**: A per-word score equal to the sum of baseline letter rates for each *distinct* letter in the word. Repeated letters do not increase the score (hard cap at first occurrence). Defined formally in DR2.
- **FCIS / functional core imperative shell**: An architectural pattern separating pure functions (no I/O, no side effects; easy to test) from the imperative code that reads files, calls those functions, and writes output. Applied here via the `letterfreq/` package split.
- **Polars**: Python DataFrame library used for frequency computation in the existing `main.py`. Not explicitly mentioned in the new ten-letter design (pure-dict functions replace DataFrame operations in the new modules), but present in the project.
- **transparency column**: A table column that shows the specific letters, bigrams, or trigrams that produced a word's score, making the ranking auditable rather than opaque.
- **per-occurrence rate**: A frequency expressed as count / total-occurrences (not count / total-words). Used as the baseline weight when scoring; defined via `to_rates()`.

## Architecture

The current single-page Zensical site is converted into a three-URL site under one project. The existing five-letter analysis moves from `docs/index.md` to `docs/five/index.md` with no behavioural changes. A new `docs/ten/index.md` hosts the ten-letter page. A new `docs/index.md` becomes a small landing page that introduces both analyses.

The ten-letter page is split into two halves:

1. **Reference tables** computed over a baseline corpus of all 3–10 letter words from dwyl/english-words: a 26-row letter frequency table, a top-100 flat bigram frequency table, and two side-by-side top-50 tables for start trigrams and end trigrams.
2. **Ranking tables** of ten-letter words: three top-50 tables ranked by letter-coverage score, bigram score, and start+end trigram score, using per-occurrence rates from the baseline as weights. Each ranking includes a transparency column showing the underlying components (which distinct letters, which top contributing bigrams, which start/end trigrams).

Python is reorganised into a small `letterfreq/` package separating pure functional core (`reference.py`, `scoring.py`) from imperative shell (entry scripts `main.py` for five-letter and `main_ten.py` for ten-letter). Both entry scripts read pre-filtered word files, call pure functions for computation, and emit HTML embedded in Markdown — the same pattern the existing `main.py` already uses.

Three word files live in `data/`: `words.txt` (current 5-letter, unchanged), `words_10.txt` (10-letter), `words_3_to_10.txt` (baseline). They are generated once by a one-shot helper script (`scripts/build_corpora.py`) that downloads the dwyl/english-words list and applies the lowercase a–z filter; outputs are committed, the helper is not run during normal builds.

Zensical is bumped from `>=0.0.28` to `>=0.0.33` (5 cumulative bug-fix releases, no migration). Navigation is defined explicitly in `zensical.toml` rather than directory-derived.

## Decision Record

### DR1: Three separate top-N tables instead of one combined score
**Status:** Accepted
**Confidence:** High
**Reevaluation triggers:** If usage shows the rankings are nearly identical (high overlap of words across the three tables), a combined score may add more value than three independent views.

**Decision:** We chose three independent top-50 tables (one per score) over a single composite score or one mega-table with sortable score columns.

**Consequences:**
- **Enables:** Each ranking is interpretable on its own. A word's strength on one dimension is visible without normalisation choices. Readers can compare lists side-by-side to see which words excel on multiple dimensions.
- **Prevents:** No single "best ten-letter word" answer — readers must synthesise across three rankings themselves.

**Alternatives considered:**
- **Single composite score:** Rejected because it forces a normalisation choice (which weights letters vs bigrams vs trigrams) that has no principled answer for this use case.
- **One sortable mega-table with all four columns:** Rejected because top-50 per criterion is the right size; a mega-table would need pagination or virtualisation, adding JS complexity for marginal benefit.

### DR2: Letter-coverage scoring uses distinct-letters-only (hard cap)
**Status:** Accepted
**Confidence:** High
**Reevaluation triggers:** If users want to see how repeated-letter words score on a smoother gradient.

**Decision:** We chose `letter_score(w) = Σ f_L(l) for l ∈ distinct(w)`. Repeated letters contribute zero to the score on their second and subsequent occurrences.

**Consequences:**
- **Enables:** The simplest interpretable formula. A word using ten distinct top-frequency letters wins by construction. The score is bounded above by the sum of all 26 letter rates (=1.0).
- **Prevents:** Words with strategic repetition (e.g., a high-frequency letter used twice with all other slots distinct) get no extra credit for the repeat.

**Alternatives considered:**
- **Diminishing returns (1/k):** Rejected as adding nuance without a clear interpretation. Users explicitly preferred the hard cap.
- **Geometric decay (½^(k−1)):** Rejected for the same reason; smoother but less interpretable.

### DR3: Baseline corpus is lengths 3–10 for letter/bigram counts; lengths 4–10 for trigram counts
**Status:** Accepted
**Confidence:** High
**Reevaluation triggers:** If readers want to see 3-letter word trigrams (e.g., `the`, `and`, `for`) represented in the start/end trigram tables, revisit the trigram lower bound.

**Decision:** We chose to filter the baseline corpus to lengths 3–10 for letter and bigram counting, but to filter to lengths 4–10 for start- and end-trigram counting.

**Consequences:**
- **Enables:** Every word of length ≥3 contributes to letter and bigram tables (preserving signal from short words). Trigram tables structurally avoid the 3-letter double-count problem: a 4-letter word's start trigram (positions 1–3) and end trigram (positions n−2, n−1, n) cannot be identical when n ≥ 4. The two trigram reference tables are therefore cleanly separable.
- **Prevents:** Three-letter words (`the`, `and`, `for`, `cat`, …) do not appear in the start/end trigram reference tables at all. Acknowledged trade-off — these are common English trigrams that some readers would expect to see, but their inclusion would conflate the start and end distributions.

**Alternatives considered:**
- **Lengths 1–10 for everything:** Rejected; 1- and 2-letter words add noise to the letter table and contribute nothing to bigram/trigram tables.
- **Lengths 3–10 for everything:** Rejected during proleptic challenge. Causes a 3-letter word's single trigram to be counted in both the start and end tables, inflating short-trigram dominance and making the two tables not cleanly comparable.
- **Lengths 4–10 for everything:** Rejected; conservative but loses meaningful 3-letter contributions to the letter and bigram tables.

### DR4: Start/end trigrams shown as two ranked top-N tables (not 26×26 grids)
**Status:** Accepted
**Confidence:** High
**Reevaluation triggers:** If readers want to drill into "trigrams beginning with a given letter pair," the grid form may be needed later.

**Decision:** We chose two side-by-side top-50 ranked tables (most common start trigrams; most common end trigrams) rather than reusing the 5-letter page's 26×26 trigram grid pattern.

**Consequences:**
- **Enables:** Scannable, immediately interpretable: the actual character sequences (`con`, `pre`, `ing`, `ion`) appear in the table. No JS-loaded drill-down required.
- **Prevents:** No way to ask "what start trigrams begin with `pr-`?" from this view. Information present in the data but not surfaced.

**Alternatives considered:**
- **26×26 heatmap grids per trigram type:** Rejected as over-engineered for a reference summary; users explicitly ruled out heavy spatial displays for ten-letter data.
- **Single combined sortable table (trigram | start_freq | end_freq | total):** Rejected as harder to scan; the side-by-side ranked layout matches the natural question ("what's a common prefix? a common suffix?").

### DR5: Pre-filtered per-page word files (not single source filtered at runtime)
**Status:** Accepted
**Confidence:** Medium
**Reevaluation triggers:** If the project ever adds 6-, 7-, 8-, or 9-letter pages, the file count grows linearly and a single-source approach becomes more attractive.

**Decision:** We chose to commit three separate pre-filtered word files (`words.txt`, `words_10.txt`, `words_3_to_10.txt`) rather than committing the full ~370k-word dwyl/english-words list and filtering at runtime.

**Consequences:**
- **Enables:** Fast script startup. Existing `data/words.txt` pattern is preserved. Each entry script knows exactly which file to load with no length-filter logic.
- **Prevents:** Adding a future word-length page requires generating and committing another file. The full source list is not in the repo, so the filtering provenance lives in `scripts/build_corpora.py` rather than being inferable from `data/`.

**Alternatives considered:**
- **Single source filtered at runtime:** Rejected as a larger commit and slightly slower load for a project that currently only needs two filtered views.
- **Single source + cached length-filtered files:** Rejected as over-engineered; caching adds complexity (`.gitignore` entries, cache invalidation) for negligible benefit.

### DR6: Top-50 per ranking table
**Status:** Accepted
**Confidence:** High
**Reevaluation triggers:** If users repeatedly ask for words below the top-50 cut, raise to top-100.

**Decision:** We chose top-50 entries per ranking table.

**Consequences:**
- **Enables:** Three tables of 50 rows each fit comfortably on one page without dominating the layout.
- **Prevents:** Long-tail exploration ("what's the 200th best word for letter coverage?") not possible from the page.

**Alternatives considered:**
- **Top-100:** Rejected as making the page top-heavy with the ranking section.
- **Top-250 with client-side sortable/filterable:** Rejected; adds JS complexity for a feature not yet requested.

### DR7: Multi-page site at `/five/` and `/ten/` with landing page at `/`
**Status:** Accepted
**Confidence:** High
**Reevaluation triggers:** If a future page (e.g., 7-letter analysis) is added, navigation may need restructuring or a section grouping.

**Decision:** We chose three URLs — `/` (landing), `/five/`, `/ten/` — over keeping the five-letter page at root.

**Consequences:**
- **Enables:** Symmetric URL structure makes the two analyses peers, not one as primary and one as secondary. A landing page can frame both analyses for first-time visitors.
- **Prevents:** Existing inbound links to the root URL no longer land on the five-letter analysis directly (they land on the landing page). Acknowledged minor regression.

**Alternatives considered:**
- **Keep five-letter at `/`, add ten-letter at `/ten/`:** Rejected; user explicitly preferred the symmetric structure.

## Existing Patterns

Investigation found the following patterns in the current codebase that this design follows:

- **Pre-filtered word files in `data/`.** The current `data/words.txt` is committed at full fidelity (one word per line, lowercase, alpha only). The new corpus files follow the same shape.
- **HTML-embedded-in-Markdown rendering.** `main.py` generates table and grid HTML as strings and embeds them in `docs/index.md`. `main_ten.py` follows the same approach for `docs/ten/index.md`.
- **Sortable tables via `js/sort-tables.js`.** Existing class `sortable-table` with `<th class="sortable" data-col="N">` headers — reused for all new tables.
- **Per-column normalisation helpers.** `_col_maxes` / `_grid_col_maxes` in `main.py` — not directly reused (no heatmaps in the new page) but the pattern of "compute column-max once, normalise cells against it" is followed for the bar columns in reference tables.
- **`.freq-table` and `.heatmap` CSS classes in `docs/css/heatmap.css`.** Reused as-is; new layout-only CSS (the side-by-side trigram pair) is appended.
- **Pure-functional computation in `main.py`.** Functions like `compute_overall_frequencies`, `compute_bigrams` are pure (input → DataFrame). The new `letterfreq/reference.py` and `letterfreq/scoring.py` formalise this separation by extracting them into their own modules.

This design introduces one new pattern: a `letterfreq/` Python package separating pure modules from entry scripts. Justified by: as the project grows from one entry script to two, sharing pure logic via a package is cleaner than cross-importing between top-level scripts.

## Implementation Phases

<!-- START_PHASE_1 -->
### Phase 1: Corpus generation and site restructuring
**Goal:** Generate the two new corpus files; restructure the existing site so the five-letter page lives at `/five/` and a landing page at `/`; bump Zensical.

**Components:**
- `scripts/build_corpora.py` — one-shot helper that downloads dwyl/english-words, applies lowercase a–z filter, writes `data/words_10.txt` and `data/words_3_to_10.txt`. Existing `data/words.txt` left untouched.
- `data/words_10.txt` — committed output, 10-letter words.
- `data/words_3_to_10.txt` — committed output, 3–10 letter baseline corpus.
- Move `docs/index.md` → `docs/five/index.md`.
- Move `docs/data/bigrams.json` and `docs/data/trigrams.json` → `docs/five/data/bigrams.json` and `docs/five/data/trigrams.json`. The JS files `sort-tables.js` and `trigram-expand.js` use bare-relative `fetch("data/bigrams.json")` and `fetch("data/trigrams.json")` (verified at `sort-tables.js:39` and `trigram-expand.js:8`); these continue to resolve correctly from `/five/index.html` once the JSON files are co-located. No JS change required.
- Update `main.py` JSON output paths: `DATA_DIR = DOCS_DIR / "five" / "data"` (replacing `DOCS_DIR / "data"`).
- New `docs/index.md` — small landing page linking to `/five/` and `/ten/` (the latter empty placeholder for now).
- New `docs/ten/index.md` — empty placeholder.
- `zensical.toml` — explicit `nav` block; `site_name` and `site_description` updated; `pyproject.toml` `zensical>=0.0.33`.
- `main.py` — output path updated from `docs/index.md` to `docs/five/index.md`.

**Dependencies:** None (first phase).

**Done when:** `uv lock` and `uv sync` succeed at the new Zensical version; `uv run zensical build --clean` succeeds; the built site has `/five/` rendering the existing five-letter analysis with all bigram and trigram drill-downs working; `/` shows the landing page; `/ten/` exists (empty); `data/words_10.txt` and `data/words_3_to_10.txt` are committed and have plausible line counts.
<!-- END_PHASE_1 -->

<!-- START_PHASE_2 -->
### Phase 2: `letterfreq` package — reference frequency module
**Goal:** Extract pure functional computation of baseline letter, bigram, start-trigram, and end-trigram frequencies into a reusable module.

**Components:**
- `letterfreq/__init__.py` — empty package marker.
- `letterfreq/reference.py` — pure functions:
  - `letter_counts(words: list[str]) -> dict[str, int]`
  - `bigram_counts(words: list[str]) -> dict[str, int]` (all consecutive pairs across all words)
  - `start_trigram_counts(words: list[str], min_length: int = 4) -> dict[str, int]` (first three letters of each word; words shorter than `min_length` are skipped — default 4 per DR3)
  - `end_trigram_counts(words: list[str], min_length: int = 4) -> dict[str, int]` (last three letters of each word; words shorter than `min_length` are skipped — default 4 per DR3)
  - `to_rates(counts: dict[str, int], total: int) -> dict[str, float]` — helper, count/total
- `tests/test_reference.py` — hand-checked tiny inputs (e.g., `["cat", "act"]` → letter counts {a:2, c:2, t:2}; bigram counts {ca:1, at:1, ac:1, ct:1}; start trigrams {cat:1, act:1}; end trigrams {cat:1, act:1}).

**Dependencies:** Phase 1.

**Covers:** ten-letter-page.AC1.1, ten-letter-page.AC1.2, ten-letter-page.AC1.3, ten-letter-page.AC1.4 (reference frequency correctness).

**Done when:** Tests in `tests/test_reference.py` pass; counts and rates verified by hand against tiny inputs; module is pure (no I/O, no globals).
<!-- END_PHASE_2 -->

<!-- START_PHASE_3 -->
### Phase 3: `letterfreq` package — scoring module
**Goal:** Implement the three scoring functions for ten-letter words, parameterised on baseline rates.

**Components:**
- `letterfreq/scoring.py` — pure functions:
  - `letter_score(word: str, letter_rates: dict[str, float]) -> float` — sum over distinct letters.
  - `bigram_score(word: str, bigram_rates: dict[str, float]) -> float` — sum over consecutive bigrams (assumes word length ≥2).
  - `trigram_score(word: str, start_rates: dict[str, float], end_rates: dict[str, float]) -> float` — start[:3] rate plus end[-3:] rate.
  - Helper: `top_n_by_score(words, score_fn, n=50) -> list[tuple[str, float]]` — sorted descending, alphabetical tie-break.
- `tests/test_scoring.py`:
  - `letter_score("aaaaaaaaaa", {"a": 0.1, ...}) == 0.1`
  - `letter_score("abcdefghij", rates) == sum(rates[l] for l in "abcdefghij")`
  - `bigram_score` on a 10-letter word with controlled rates produces the expected sum of 9 terms.
  - `trigram_score` with controlled start/end rates produces the expected sum.
  - Tie-break: two words with equal scores returned in alphabetical order.

**Dependencies:** Phase 2 (uses the rate dicts produced by `reference.py`).

**Covers:** ten-letter-page.AC2.1, ten-letter-page.AC2.2, ten-letter-page.AC2.3, ten-letter-page.AC2.4, ten-letter-page.AC3.1 (scoring formula correctness; tie-break stability).

**Done when:** All `test_scoring.py` cases pass; module is pure; functions accept rate dicts as parameters (no implicit baseline).
<!-- END_PHASE_3 -->

<!-- START_PHASE_4 -->
### Phase 4: Reference-table rendering
**Goal:** Render the three reference-table HTML blocks for the ten-letter page.

**Components:**
- `letterfreq/render.py` (new module):
  - `render_letter_table(rates, counts, word_count) -> str` — 26-row sortable table, columns letter/count/per-word-rate/bar.
  - `render_bigram_table(rates, counts, word_count, top_n=100) -> str` — flat top-100 sortable table.
  - `render_trigram_pair(start_rates, start_counts, end_rates, end_counts, word_count, top_n=50) -> str` — two side-by-side top-50 tables wrapped in a flex/grid container.
- `docs/css/heatmap.css` — append rules for the new two-column trigram-pair layout (`.trigram-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }` plus narrow-viewport stack-down).

**Dependencies:** Phase 2 (rates), Phase 1 (CSS file exists).

**Covers:** ten-letter-page.AC4.1, ten-letter-page.AC4.2, ten-letter-page.AC4.3, ten-letter-page.AC4.4 (reference tables render with correct shape and sort behaviour).

**Done when:** Rendering functions called from a smoke test produce well-formed HTML containing the expected number of rows; sortable-table CSS class is applied; manual visual check against `uv run zensical serve` shows the tables look correct on `/ten/` (still empty page logic — content can be inserted manually for the visual check).
<!-- END_PHASE_4 -->

<!-- START_PHASE_5 -->
### Phase 5: Ranking-table rendering
**Goal:** Render the three top-50 ranking tables of ten-letter words with transparency columns.

**Components:**
- `letterfreq/render.py` (extended):
  - `render_letter_ranking(words_10, letter_rates, top_n=50) -> str` — columns: rank, word, distinct letters (sorted by individual rate), score.
  - `render_bigram_ranking(words_10, bigram_rates, top_n=50) -> str` — columns: rank, word, top-3 contributing bigrams (by `rate × per-word count`), score.
  - `render_trigram_ranking(words_10, start_rates, end_rates, top_n=50) -> str` — columns: rank, word, start trigram, end trigram, score.

**Dependencies:** Phase 3 (scoring), Phase 4 (HTML helper conventions).

**Covers:** ten-letter-page.AC5.1, ten-letter-page.AC5.2, ten-letter-page.AC5.3, ten-letter-page.AC5.4 (ranking tables render with correct columns including transparency; sortable behaviour).

**Done when:** Rendering functions produce well-formed HTML with exactly top_n rows; transparency columns show the expected components (verifiable against a hand-checked example word); all three tables use the `sortable-table` class.
<!-- END_PHASE_5 -->

<!-- START_PHASE_6 -->
### Phase 6: `main_ten.py` orchestration
**Goal:** Wire reference computation, scoring, and rendering into the imperative shell that emits the ten-letter page.

**Components:**
- `main_ten.py`:
  - Load `data/words_10.txt` (10-letter words).
  - Load `data/words_3_to_10.txt` (baseline).
  - Call `letterfreq.reference` to compute baseline rates.
  - Call `letterfreq.render` for all six tables (3 reference + 3 ranking).
  - Compose `docs/ten/index.md` with frontmatter, page title, intro paragraph, two H2 sections ("Baseline frequencies", "Ten-letter words"), and the table blocks.
- `docs/index.md` (landing) — finalise wording with project description and the two links.
- `pyproject.toml` — add `[project.scripts]` entries if useful; or document running via `uv run python main_ten.py`.

**Dependencies:** Phases 4 and 5.

**Covers:** ten-letter-page.AC6.1, ten-letter-page.AC6.2 (page builds end-to-end; correct content present).

**Done when:** `uv run python main_ten.py && uv run zensical build --clean` produces a `/ten/` page with all six tables populated and rendering correctly; `/five/` still renders correctly; `/` renders landing page; sortable interactions work on the new tables (manual check).
<!-- END_PHASE_6 -->

<!-- START_PHASE_7 -->
### Phase 7: Documentation update and freshness
**Goal:** Bring project context and dependency rationale up to date.

**Components:**
- `CLAUDE.md` — update project structure block to reflect `docs/five/`, `docs/ten/`, `letterfreq/` package, new corpus files, and new scripts; refresh the freshness date stamp; expand the architecture paragraph to describe both pages.
- `dependency-rationale.md` (repo root) — verify no new direct dependency was added (Zensical version bump alone does not need a new entry; Polars and Zensical entries already exist).
- `tests/` — verify existing five-letter tests still pass under the new directory layout; add `tests/test_corpora.py` asserting `words_10.txt` is non-empty and contains only 10-letter lowercase a–z entries; same shape for `words_3_to_10.txt` with length range 3–10.

**Dependencies:** Phase 6.

**Covers:** ten-letter-page.AC7.1, ten-letter-page.AC7.2 (documentation freshness; corpus file invariants).

**Done when:** `uv run pytest` passes all tests; `CLAUDE.md` accurately describes the new layout; freshness date updated; `dependency-rationale.md` (repo root) is current.
<!-- END_PHASE_7 -->

## Additional Considerations

**Corpus provenance is in code, not data.** `scripts/build_corpora.py` is the only artefact that records how the committed `words_10.txt` and `words_3_to_10.txt` were derived from dwyl/english-words. This script must remain runnable so that the corpus files can be regenerated from a known source; treat it as part of the supply chain even though it is not invoked during normal builds.

**Static-first preserved.** No JS-loaded data is required for the ten-letter page. All six tables are static HTML; sorting happens client-side via the existing `sort-tables.js`. The page is fully functional with JS disabled (sort buttons inert but content readable).

**Forward extensibility deferred.** The decision to use pre-filtered per-page word files (DR5) optimises for the current scope (2 pages). If 6/7/8/9-letter pages are added later, that decision should be revisited — the linear growth in committed files becomes a maintenance cost.
