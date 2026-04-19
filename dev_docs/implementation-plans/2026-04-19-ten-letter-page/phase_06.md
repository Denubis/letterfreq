# Ten-Letter Page Implementation Plan — Phase 6: `main_ten.py` orchestration

**Goal:** Wire reference computation, scoring, and rendering into the imperative shell that emits `docs/ten/index.md`. This is the integration phase that makes `/ten/` a real, populated page.

**Architecture:** `main_ten.py` is a thin imperative shell (FCIS pattern): it reads two pre-filtered corpus files, calls into pure modules in `letterfreq/`, and composes the final Markdown document. No business logic in this file — only orchestration.

**Tech Stack:** Python 3.14+, Zensical >=0.0.33. No new dependencies.

**Scope:** Phase 6 of 7 from `/home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md`.

**Codebase verified:** 2026-04-19. After Phases 1–5: `data/words_10.txt` and `data/words_3_to_10.txt` exist and are committed; `letterfreq/{__init__,reference,scoring,render}.py` exist with their tested functions; `docs/ten/index.md` is a placeholder. `docs/index.md` (landing) was created in Phase 1; this phase adds polish if needed.

**Phase Type:** functionality

---

## Acceptance Criteria Coverage

This phase implements and tests:

### Integration coverage (composes ACs implemented in earlier phases)
- **ten-letter-page.AC1.4 Success:** `letter_counts` and `bigram_counts` on the actual `words_3_to_10.txt` corpus produce non-zero counts for every letter a–z. (Phase 2 already covered this in unit tests; Phase 6 exercises it end-to-end.)
- **ten-letter-page.AC10.4 Success:** `first_letter_counts` and `last_letter_counts` on the actual `words_3_to_10.txt` corpus produce non-zero counts for at least the common starting/ending letters. (Phase 2 unit tests; Phase 6 end-to-end.)

### Site structure
- **ten-letter-page.AC7.1 Success:** `uv run zensical build --clean` succeeds with `zensical>=0.0.33`. (End-to-end with real `/ten/` content.)
- **ten-letter-page.AC7.2 Success:** `/five/` renders with bigram drill-downs and trigram expansions still working.
- **ten-letter-page.AC7.3 Success:** `/` shows the landing page with links to `/five/` and `/ten/`.
- **ten-letter-page.AC7.5 Success:** Dark/light toggle and `navigation.instant` behave on both pages.

(AC7.4 nav block was verified in Phase 1; Phases 2–5 don't touch zensical.toml.)

---

## Implementation Tasks

<!-- START_TASK_1 -->
### Task 1: Create `main_ten.py` orchestrator

**Verifies (when paired with Task 2):** integration of all earlier phases — produces the populated `/ten/` page.

**Files:**
- Create: `/home/brian/llm/letterfreq/main_ten.py`

**Implementation:**

```python
"""Generate docs/ten/index.md — the ten-letter analysis page.

Imperative shell only: reads pre-filtered corpus files, computes baseline
rates via letterfreq.reference, ranks ten-letter words via letterfreq.scoring,
renders HTML tables via letterfreq.render, and writes the composed Markdown
document. All side effects live here; pure logic lives in letterfreq/.
"""

from __future__ import annotations

from pathlib import Path

from letterfreq.reference import (
    bigram_counts,
    end_trigram_counts,
    first_letter_counts,
    last_letter_counts,
    letter_counts,
    start_trigram_counts,
    to_rates,
)
from letterfreq.render import (
    render_bigram_ranking,
    render_bigram_table,
    render_first_last_pair,
    render_letter_ranking,
    render_letter_table,
    render_positional_ranking,
    render_trigram_pair,
    render_trigram_ranking,
)

REPO_ROOT = Path(__file__).parent
DATA_DIR = REPO_ROOT / "data"
WORDS_10_FILE = DATA_DIR / "words_10.txt"
BASELINE_FILE = DATA_DIR / "words_3_to_10.txt"
INDEX_MD = REPO_ROOT / "docs" / "ten" / "index.md"


def load_words(path: Path) -> list[str]:
    """Read one-word-per-line corpus file; drop empty lines; dedupe (preserve order).

    Defensive dedupe via dict.fromkeys protects ranking from showing the same
    word twice if the corpus file contains duplicates (Phase 5 deferred
    concern #3; complementary uniqueness assertion lives in Phase 7).
    """
    return list(dict.fromkeys(w for w in path.read_text().splitlines() if w))


def _count_baseline(baseline: list[str]) -> dict[str, dict[str, int]]:
    """Compute all six baseline count dicts from the corpus.

    Returned keys: 'letter', 'bigram', 'start_trigram', 'end_trigram',
    'first_letter', 'last_letter'. Pure; suitable for direct testing.
    """
    return {
        "letter": letter_counts(baseline),
        "bigram": bigram_counts(baseline),
        "start_trigram": start_trigram_counts(baseline),  # default min_length=4
        "end_trigram": end_trigram_counts(baseline),
        "first_letter": first_letter_counts(baseline),
        "last_letter": last_letter_counts(baseline),
    }


def _compute_rates(
    counts: dict[str, dict[str, int]],
    word_total: int,
) -> dict[str, dict[str, float]]:
    """Convert count dicts into rate dicts using the production denominator choices.

    Per-occurrence rate (sum-of-counts denominator) for letter / bigram /
    start_trigram / end_trigram. Per-word rate (`word_total` denominator) for
    first_letter / last_letter (per DR8: every baseline word contributes
    exactly one first and one last letter).

    Each returned rate dict sums to 1.0 by construction. Factoring this out
    of generate_page lets tests assert the production-path denominator
    choices rather than re-deriving them in test setup (Phase 5 deferred
    concern #1; closes the regression-guard gap from Phase 2).
    """
    return {
        "letter": to_rates(counts["letter"], sum(counts["letter"].values())),
        "bigram": to_rates(counts["bigram"], sum(counts["bigram"].values())),
        # Trigram totals: only words of length >= 4 contributed (default
        # min_length=4 per DR3). Sum-of-counts equals the count of length-≥4
        # words. Critical: using `word_total` here would systematically
        # deflate trigram rates by the proportion of length-3 words.
        "start_trigram": to_rates(
            counts["start_trigram"], sum(counts["start_trigram"].values())
        ),
        "end_trigram": to_rates(
            counts["end_trigram"], sum(counts["end_trigram"].values())
        ),
        "first_letter": to_rates(counts["first_letter"], word_total),
        "last_letter": to_rates(counts["last_letter"], word_total),
    }


def generate_page(words_10: list[str], baseline: list[str]) -> str:
    """Compose the full docs/ten/index.md content."""
    # --- Counts and rates over baseline -----------------------------------
    counts = _count_baseline(baseline)
    word_total = len(baseline)
    rates = _compute_rates(counts, word_total)

    letter_c = counts["letter"]
    bigram_c = counts["bigram"]
    start_c = counts["start_trigram"]
    end_c = counts["end_trigram"]
    first_c = counts["first_letter"]
    last_c = counts["last_letter"]

    letter_r = rates["letter"]
    bigram_r = rates["bigram"]
    start_r = rates["start_trigram"]
    end_r = rates["end_trigram"]
    first_r = rates["first_letter"]
    last_r = rates["last_letter"]

    # trigram_word_total only used as the `word_count` argument to
    # render_trigram_pair (drives its "Per word" column).
    trigram_word_total = sum(start_c.values())  # == sum(end_c.values())

    # --- Reference tables --------------------------------------------------
    # The `word_count` argument to each renderer drives the "Per word" rate
    # column displayed in the table. We use:
    #   - `word_total` (full baseline) for letter, bigram, first/last tables
    #     because every baseline word contributed to those counts.
    #   - `trigram_word_total` (length-≥4 words only) for the trigram pair so
    #     the displayed rate matches the population that actually contributed
    #     to the count, consistent with start_r / end_r above.
    ref_letter = render_letter_table(letter_r, letter_c, word_total)
    ref_bigram = render_bigram_table(bigram_r, bigram_c, word_total, top_n=100)
    ref_trigram = render_trigram_pair(
        start_r, start_c, end_r, end_c, trigram_word_total, top_n=50
    )
    ref_first_last = render_first_last_pair(
        first_r, first_c, last_r, last_c, word_total
    )

    # --- Ranking tables (over the 10-letter words) -------------------------
    rank_letter = render_letter_ranking(words_10, letter_r, top_n=50)
    rank_bigram = render_bigram_ranking(words_10, bigram_r, top_n=50)
    rank_trigram = render_trigram_ranking(words_10, start_r, end_r, top_n=50)
    rank_positional = render_positional_ranking(words_10, first_r, last_r, top_n=50)

    return (
        "---\n"
        "icon: null\n"
        "---\n\n"
        "# Ten-Letter Word Frequencies\n\n"
        f"Reference frequencies computed over **{word_total:,}** English words "
        f"of length 3–10 (the baseline corpus). Rankings cover **{len(words_10):,}** "
        f"ten-letter words. All tables sortable by clicking column headers.\n\n"
        "## Baseline frequencies\n\n"
        "### Letter frequency\n\n"
        f"{ref_letter}\n\n"
        "### Bigram frequency (top 100)\n\n"
        f"{ref_bigram}\n\n"
        "### Start and end trigrams (top 50 each)\n\n"
        f"{ref_trigram}\n\n"
        "### First and last letters\n\n"
        f"{ref_first_last}\n\n"
        "## Ten-letter words\n\n"
        "Note: the reference tables above show **per-word rates** (fraction "
        "of baseline words containing each item). The scoring formulas below "
        "use **per-occurrence rates** (fraction of all letter / bigram / "
        "trigram occurrences across the baseline). Same baseline corpus, "
        "different denominators — so a letter like `e` appears with two "
        "different numbers across the page. Both are correct for their "
        "respective question.\n\n"
        "### Top 50 by letter coverage\n\n"
        "Score = sum of baseline rates over the **distinct** letters in the word. "
        "Words that pack many high-frequency letters score highest; repeats add "
        "nothing.\n\n"
        f"{rank_letter}\n\n"
        "### Top 50 by bigram score\n\n"
        "Score = sum of baseline bigram rates over the 9 consecutive bigram "
        "positions. Repeated bigrams contribute each time they occur.\n\n"
        f"{rank_bigram}\n\n"
        "### Top 50 by start + end trigram\n\n"
        "Score = baseline rate of the word's start trigram (positions 1–3) + "
        "baseline rate of the word's end trigram (positions 8–10).\n\n"
        f"{rank_trigram}\n\n"
        "### Top 50 by positional first + last letter\n\n"
        "Score = baseline rate of the word's first letter + baseline rate of "
        "the word's last letter. Both contribute even when they're the same "
        "letter (no distinct cap).\n\n"
        f"{rank_positional}\n"
    )


def main() -> None:
    words_10 = load_words(WORDS_10_FILE)
    baseline = load_words(BASELINE_FILE)
    page = generate_page(words_10, baseline)
    INDEX_MD.parent.mkdir(parents=True, exist_ok=True)
    INDEX_MD.write_text(page)
    print(
        f"Generated {INDEX_MD} "
        f"({len(words_10):,} ten-letter words, {len(baseline):,} baseline words)"
    )


if __name__ == "__main__":
    main()
```

**Implementation notes:**
- The denominator choices are encapsulated in `_compute_rates` so each rate dict sums to 1.0:
  - `'letter'`, `'bigram'` → `sum(counts.values())` (per-occurrence rate).
  - `'start_trigram'`, `'end_trigram'` → `sum(counts.values())` (equals count of length-≥4 words per DR3's default `min_length=4`). **Critical:** using `word_total` here would systematically deflate trigram rates.
  - `'first_letter'`, `'last_letter'` → `word_total` (per DR8 every baseline word contributes exactly one first and one last letter).
- `_count_baseline` and `_compute_rates` are factored out so Task 3 can assert directly against the production-path rate dicts (closes the Phase 5 deferred-concern #1 regression-guard gap).
- `load_words` deduplicates via `dict.fromkeys` (Phase 5 deferred concern #3). Phase 7 will add a complementary corpus-file uniqueness assertion.
- `trigram_word_total` is retained in `generate_page` only as the `word_count` argument to `render_trigram_pair` (drives the displayed "Per word" column).
- All four scoring metrics end up in the same probability-magnitude range.
- Module-level constants mirror the pattern in existing `main.py`.
- `generate_page` is pure (no I/O), making it directly testable via Task 3.

**No commit yet** — wait for Task 2 verification.
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: End-to-end verification (build, inspect, sanity-check)

**No file changes — verification only.**

**Implementation:**

Run the full pipeline:

```bash
uv run python main.py            # regenerates /five/ from existing main.py
uv run python main_ten.py        # generates /ten/ for the first time with real content
uv run zensical build --clean
```

Expected:
- `main.py` prints `Generated /home/brian/llm/letterfreq/docs/five/index.md (15921 words, 79605 total letters)`.
- `main_ten.py` prints `Generated /home/brian/llm/letterfreq/docs/ten/index.md (~30000 ten-letter words, ~250000 baseline words)` (counts depend on the upstream corpus snapshot).
- `zensical build` succeeds.

Inspect `site/`:

```bash
find site -name 'index.html' | sort
```

Expected:
```
site/index.html
site/five/index.html
site/ten/index.html
```

Confirm `site/ten/index.html` is large (the page has 8 tables; expect tens of KB):

```bash
ls -lh site/ten/index.html
```

Expected: file size ≥ 50 KB (4 reference tables, 4 ranking tables × 50 rows).

Confirm dev docs are NOT present:

```bash
find site \( -path '*dev_docs*' -o -path '*design-plans*' -o -path '*architecture*' -o -path '*implementation-plans*' \) -print
```

Expected: no output.

Run the full pytest suite (`python -m pytest` bypasses rtk's bare-`pytest` interception which returns a false "no tests collected"):

```bash
uv run python -m pytest -q
```

Expected: all tests pass — Phase 1–5 baseline (79 tests) plus the new `test_main_ten.py` from Task 3 (9 tests) → **88 tests total**.

**Visual sanity check (manual):**

Run the dev server:

```bash
uv run zensical serve
```

Open http://localhost:8000 and verify:
1. **Landing page (`/`):** Shows the project intro and links to `/five/` and `/ten/`.
2. **Five-letter (`/five/`):** Existing five-letter analysis. Click a bigram cell — drill-down panel appears below the grid (proves `fetch("data/bigrams.json")` resolves correctly under `/five/`). Click a trigram cell — completion list appears. Sort columns work.
3. **Ten-letter (`/ten/`):**
   - Letter frequency table: 26 rows, sortable.
   - Bigram top-100 table: exactly 100 rows, sortable.
   - Start/end trigram pair: side-by-side at desktop width, stacked at mobile width.
   - First/last letter pair: 26 rows each side, side-by-side at desktop width.
   - Four ranking tables: 50 rows each. Spot-check: a high-letter-coverage word should contain many of {e, t, a, o, i, n}. Doubled-endpoint check: scan the positional ranking for any 10-letter word whose first and last letters match (if one is in the corpus); both letters should still contribute to its score, per DR8 (no distinct cap on endpoints).
   - Bigram transparency: Task 3's `test_top10_bigram_transparency_covers_majority` enforces the 50% rule (top-3 contributors must cover ≥50% of total bigram score for every top-10 word). If that test fails, bump the cap from 3 to 5 in `render_bigram_ranking` and re-run `main_ten.py` + `zensical build` before completing the visual check. No manual vibes-judgment needed.
4. **Theme toggle:** Light/dark mode switch works on all three pages.
5. **Instant navigation:** Clicking nav links between pages doesn't full-reload (URL bar updates without flicker; `navigation.instant` working).

**Commit:**

```bash
git add main_ten.py docs/ten/index.md
git commit -m "feat: main_ten.py — generate populated /ten/ page (4 reference + 4 ranking tables)"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Add `tests/test_main_ten.py` — production-path tests

**Verifies three things:**
1. The actual rate dicts produced inside `generate_page` (via `_compute_rates`) sum to 1.0 with the chosen denominators — closes the Phase 5 deferred concern #1 regression-guard gap by calling the production helper rather than re-deriving rates inside the test.
2. `load_words` deduplicates — Phase 5 deferred concern #3 (defensive in-process guard against duplicate corpus entries).
3. The bigram top-3 transparency rule holds for all top-10 ranked words — Phase 5 deferred concern #2. Hard assertion: if any top-10 word's top-3 bigram contributions sum to less than 50% of its total bigram score, the test fails and the implementer must bump the cap to 5 in `render_bigram_ranking`.

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_main_ten.py`

**Implementation:**

```python
"""Production-path tests for main_ten.generate_page and its helpers.

Closes three Phase 5 deferred concerns:
  1. Rate dicts produced by _compute_rates sum to 1.0 (denominator regression
     guard — calls the production helper, not a re-derivation).
  2. load_words deduplicates input lines.
  3. Top-3 bigram transparency covers ≥50% of total score for every top-10
     ranked word (forces a cap bump if violated).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from letterfreq.scoring import bigram_score, top_n_by_score
from main_ten import (
    WORDS_10_FILE,
    _compute_rates,
    _count_baseline,
    load_words,
)

BASELINE_PATH = Path(__file__).parent.parent / "data" / "words_3_to_10.txt"


@pytest.fixture(scope="module")
def baseline_words() -> list[str]:
    if not BASELINE_PATH.exists():
        pytest.skip(f"baseline corpus not present: {BASELINE_PATH}")
    return [w for w in BASELINE_PATH.read_text().splitlines() if w]


@pytest.fixture(scope="module")
def production_rates(baseline_words: list[str]) -> dict[str, dict[str, float]]:
    """The exact rate dicts generate_page consumes, via the production helper."""
    return _compute_rates(_count_baseline(baseline_words), len(baseline_words))


# --- Concern #1: rate dicts sum to 1.0 (production path) -----------------------


@pytest.mark.parametrize(
    "key",
    [
        "letter",
        "bigram",
        "start_trigram",
        "end_trigram",
        "first_letter",
        "last_letter",
    ],
)
def test_production_rates_sum_to_one(
    production_rates: dict[str, dict[str, float]], key: str
) -> None:
    """Regression guard: every rate dict generate_page uses must sum to 1.0.

    The classic denominator bug surfaced during plan review was using
    `len(baseline)` instead of `sum(start_trigram_counts.values())` for the
    trigram rate, which would systematically deflate trigram rates by the
    proportion of length-3 words. This parametrised test catches any future
    occurrence by exercising the production helper directly.
    """
    rates = production_rates[key]
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9), (
        f"{key} rates sum to {sum(rates.values())!r}, not 1.0 — "
        "denominator choice in _compute_rates is wrong."
    )


# --- Concern #3: load_words deduplicates --------------------------------------


def test_load_words_deduplicates_preserving_order(tmp_path: Path) -> None:
    """If the corpus file ever contains duplicates, ranking must not show the
    same word twice. Order of first occurrence is preserved.
    """
    p = tmp_path / "dups.txt"
    p.write_text("apple\nbanana\napple\ncherry\nbanana\napple\n")
    assert load_words(p) == ["apple", "banana", "cherry"]


def test_load_words_drops_empty_lines(tmp_path: Path) -> None:
    p = tmp_path / "spaced.txt"
    p.write_text("a\n\nb\n\n\nc\n")
    assert load_words(p) == ["a", "b", "c"]


# --- Concern #2: bigram top-3 transparency covers majority --------------------


def test_top10_bigram_transparency_covers_majority(
    baseline_words: list[str],
    production_rates: dict[str, dict[str, float]],
) -> None:
    """For every top-10 ranked ten-letter word, the top-3 bigram contributions
    must sum to ≥50% of that word's total bigram score. If this fails, the
    transparency cap of 3 in render_bigram_ranking is hiding more than half
    of the score's justification — bump it to 5 in render.py and re-render.
    """
    if not WORDS_10_FILE.exists():
        pytest.skip(f"ten-letter corpus not present: {WORDS_10_FILE}")
    words_10 = load_words(WORDS_10_FILE)
    bigram_r = production_rates["bigram"]

    def score(word: str) -> float:
        return bigram_score(word, bigram_r)

    top10 = top_n_by_score(words_10, score, n=10)
    failures: list[str] = []
    for word, total in top10:
        if total <= 0:
            continue  # nothing to attribute
        per_word_bigrams = Counter(word[i : i + 2] for i in range(len(word) - 1))
        contribs = sorted(
            (bigram_r.get(bg, 0.0) * cnt for bg, cnt in per_word_bigrams.items()),
            reverse=True,
        )
        top3_sum = sum(contribs[:3])
        ratio = top3_sum / total
        if ratio < 0.5:
            failures.append(
                f"  {word!r}: top-3 covers {ratio:.1%} "
                f"({top3_sum:.4f} / {total:.4f})"
            )
    assert not failures, (
        "Top-3 bigram transparency hides too much for the following top-10 "
        "ranked words. Bump the cap from 3 to 5 in render_bigram_ranking and "
        "re-run main_ten.py + zensical build:\n" + "\n".join(failures)
    )
```

**Verification:**

```bash
uv run python -m pytest tests/test_main_ten.py -v
```

Expected: 9 tests pass (6 parametrised rate tests + 2 dedupe/empty-line tests + 1 transparency test).

**If `test_top10_bigram_transparency_covers_majority` fails:** edit `letterfreq/render.py` and change `[:3]` to `[:5]` in `render_bigram_ranking` (search for the `contribs = sorted(...)[:3]` slice). Re-run `uv run python main_ten.py` and `uv run zensical build --clean`. Re-run the test. Commit the cap change as a separate commit before the test commit.

**Commit:**

```bash
git add tests/test_main_ten.py
git commit -m "test: production-path rate sums + load_words dedupe + top-3 bigram transparency"
```
<!-- END_TASK_3 -->

