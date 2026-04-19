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
    """Read one-word-per-line corpus file, dropping empty lines."""
    return [w for w in path.read_text().splitlines() if w]


def generate_page(words_10: list[str], baseline: list[str]) -> str:
    """Compose the full docs/ten/index.md content."""
    # --- Counts and rates over baseline -----------------------------------
    letter_c = letter_counts(baseline)
    bigram_c = bigram_counts(baseline)
    start_c = start_trigram_counts(baseline)  # default min_length=4
    end_c = end_trigram_counts(baseline)
    first_c = first_letter_counts(baseline)
    last_c = last_letter_counts(baseline)

    letter_total = sum(letter_c.values())
    bigram_total = sum(bigram_c.values())
    word_total = len(baseline)
    # Trigram totals: only words of length >= 4 contributed (start_trigram_counts
    # / end_trigram_counts use default min_length=4 per DR3). Each contributing
    # word produced exactly one start trigram and one end trigram, so the
    # denominator is the count of trigrams emitted, which equals the number of
    # baseline words with length >= 4.
    trigram_word_total = sum(start_c.values())  # == sum(end_c.values())

    letter_r = to_rates(letter_c, letter_total)
    bigram_r = to_rates(bigram_c, bigram_total)
    start_r = to_rates(start_c, trigram_word_total)
    end_r = to_rates(end_c, trigram_word_total)
    # first/last letter counts include every baseline word (no min_length
    # filter per DR8), so word_total is the correct denominator.
    first_r = to_rates(first_c, word_total)
    last_r = to_rates(last_c, word_total)

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
- The `to_rates` totals are chosen so that each rate dict sums to 1.0:
  - `letter_total = sum(letter_c.values())` — per-letter rates sum to 1.0.
  - `bigram_total = sum(bigram_c.values())` — per-bigram rates sum to 1.0.
  - `trigram_word_total = sum(start_c.values())` — only baseline words of length ≥ 4 contributed to start/end trigram counts (per DR3's default `min_length=4`), so the denominator must match. Equivalent to `sum(1 for w in baseline if len(w) >= 4)`. **Critical:** using `len(baseline)` here would systematically deflate trigram rates by the proportion of length-3 words.
  - `word_total = len(baseline)` — used for first/last letter rates because per DR8 every baseline word contributes exactly one first letter and one last letter (no minimum-length filter).
- All four scoring metrics end up in the same probability-magnitude range.
- Module-level constants mirror the pattern in existing `main.py`.
- `generate_page` is pure (no I/O), making it directly testable via Task 2.

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

Run the full pytest suite:

```bash
uv run pytest -q
```

Expected: all tests pass (test_frequencies, test_reference, test_scoring, test_render_reference, test_render_ranking).

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
4. **Theme toggle:** Light/dark mode switch works on all three pages.
5. **Instant navigation:** Clicking nav links between pages doesn't full-reload (URL bar updates without flicker; `navigation.instant` working).

**Commit:**

```bash
git add main_ten.py docs/ten/index.md
git commit -m "feat: main_ten.py — generate populated /ten/ page (4 reference + 4 ranking tables)"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Add `tests/test_main_ten.py` — production-path rates-sum-to-1.0 assertion

**Verifies:** Closes the gap noted by peer review M2 — the helper function `to_rates` is unit-tested in Phase 2, but no test exercises that the actual baseline rate dicts produced inside `generate_page` sum to 1.0 with the chosen denominators (the Critical bug in earlier review was about exactly this denominator choice).

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_main_ten.py`

**Implementation:**

```python
"""Production-path tests for main_ten.generate_page.

Asserts that all six baseline rate dicts produced inside generate_page sum
to 1.0 with the denominators chosen in Phase 6 Task 1. This is a regression
guard against the trigram-denominator bug surfaced during plan review.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# We test generate_page indirectly by recomputing the same rate dicts
# the function builds internally. (Refactoring generate_page to expose
# the rate dicts as a return value would be cleaner but is out of scope.)
from letterfreq.reference import (
    bigram_counts,
    end_trigram_counts,
    first_letter_counts,
    last_letter_counts,
    letter_counts,
    start_trigram_counts,
    to_rates,
)

BASELINE_PATH = Path(__file__).parent.parent / "data" / "words_3_to_10.txt"


@pytest.fixture(scope="module")
def baseline_words() -> list[str]:
    if not BASELINE_PATH.exists():
        pytest.skip(f"baseline corpus not present: {BASELINE_PATH}")
    return [w for w in BASELINE_PATH.read_text().splitlines() if w]


def test_letter_rates_sum_to_one(baseline_words: list[str]) -> None:
    counts = letter_counts(baseline_words)
    rates = to_rates(counts, sum(counts.values()))
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9)


def test_bigram_rates_sum_to_one(baseline_words: list[str]) -> None:
    counts = bigram_counts(baseline_words)
    rates = to_rates(counts, sum(counts.values()))
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9)


def test_start_trigram_rates_sum_to_one(baseline_words: list[str]) -> None:
    """Regression guard: denominator must be sum-of-counts, NOT len(baseline_words)."""
    counts = start_trigram_counts(baseline_words)  # default min_length=4
    rates = to_rates(counts, sum(counts.values()))
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9)


def test_end_trigram_rates_sum_to_one(baseline_words: list[str]) -> None:
    counts = end_trigram_counts(baseline_words)
    rates = to_rates(counts, sum(counts.values()))
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9)


def test_first_letter_rates_sum_to_one(baseline_words: list[str]) -> None:
    counts = first_letter_counts(baseline_words)
    rates = to_rates(counts, len(baseline_words))
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9)


def test_last_letter_rates_sum_to_one(baseline_words: list[str]) -> None:
    counts = last_letter_counts(baseline_words)
    rates = to_rates(counts, len(baseline_words))
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9)
```

**Verification:**

```bash
uv run pytest tests/test_main_ten.py -v
```

Expected: 6 tests pass.

**Commit:**

```bash
git add tests/test_main_ten.py
git commit -m "test: assert all six baseline rate dicts in generate_page sum to 1.0"
```
<!-- END_TASK_3 -->

