# Ten-Letter Page Implementation Plan — Phase 5: Ranking-table rendering

**Goal:** Extend `letterfreq/render.py` with the four ten-letter ranking-table renderers (letter-coverage, bigram, start+end trigram, positional first+last). Each ranking is a sortable top-50 table with a transparency column showing the components that drove each word's score.

**Architecture:** Pure Python string-builders, same module and conventions as Phase 4. Each renderer takes `(words_10, *rate_dicts, top_n=50)`, computes per-word scores via `letterfreq.scoring`, sorts via `top_n_by_score`, and emits HTML.

**Tech Stack:** Python 3.14+, pytest. No new dependencies.

**Scope:** Phase 5 of 7 from `/home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md`.

**Codebase verified:** 2026-04-19. `letterfreq/render.py` exists after Phase 4 with `_bar_cell`, `_render_ranked_dict_table`, and the four reference renderers. `letterfreq/scoring.py` exists after Phase 3 with the four scoring functions and `top_n_by_score`.

**Phase Type:** functionality

---

## Acceptance Criteria Coverage

This phase implements and tests:

### ten-letter-page.AC6: Ranking tables render correctly on /ten/
- **ten-letter-page.AC6.1 Success:** Letter-coverage ranking table has 50 rows; transparency column lists the distinct letters of each word, sorted by individual letter rate.
- **ten-letter-page.AC6.2 Success:** Bigram ranking table has 50 rows; transparency column lists the 3 bigrams from the word that contribute most to its score, where contribution = bigram_rate × number_of_times_that_bigram_appears_in_the_word.
- **ten-letter-page.AC6.3 Success:** Trigram ranking table has 50 rows with separate start-trigram and end-trigram columns.
- **ten-letter-page.AC6.4 Success:** All four ranking tables sortable.
- **ten-letter-page.AC6.5 Success:** Positional first+last ranking table has 50 rows with separate first-letter and last-letter columns plus the score; transparency is direct (the two letters shown are the inputs to the score formula).

---

## Implementation Tasks

<!-- START_SUBCOMPONENT_A (tasks 1-2) -->
<!-- START_TASK_1 -->
### Task 1: Extend `letterfreq/render.py` with the four ranking-table renderers

**Verifies (when paired with Task 2 tests):** ten-letter-page.AC6.1, AC6.2, AC6.3, AC6.4, AC6.5.

**Files:**
- Modify: `/home/brian/llm/letterfreq/letterfreq/render.py` (append after the existing reference-table functions)

**Implementation:**

Two-part change:

**Part A — add imports at the TOP of `letterfreq/render.py` (after the existing imports from Phase 4):**

```python
from collections import Counter as _Counter

from letterfreq.scoring import (
    bigram_score,
    letter_score,
    positional_endpoint_score,
    top_n_by_score,
    trigram_score,
)
```

(All Python imports are top-level for module load; placing them mid-file would only confuse readers and trigger `ruff E402`.)

**Part B — append the following at the end of `letterfreq/render.py`:**

```python


# --- Ranking-table renderers (Phase 5) ----------------------------------------


def _ranking_thead(columns: list[str]) -> str:
    """Render a sortable <thead> from a list of column headings."""
    cells = "".join(
        f'<th class="sortable" data-col="{i}">{escape(col)}</th>'
        for i, col in enumerate(columns)
    )
    return f"  <thead><tr>{cells}</tr></thead>\n"


def render_letter_ranking(
    words_10: list[str],
    letter_rates: dict[str, float],
    top_n: int = 50,
) -> str:
    """Top-N ten-letter words by letter_score, with distinct-letter transparency.

    Columns: Rank | Word | Distinct letters | Score.
    The 'distinct letters' column lists the unique letters in the word, sorted
    descending by their individual rate (highest-rate letter first).
    """
    score_fn = lambda word: letter_score(word, letter_rates)
    ranked = top_n_by_score(words_10, score_fn, n=top_n)
    rows: list[str] = []
    for rank, (word, score) in enumerate(ranked, start=1):
        distinct_sorted = sorted(
            set(word), key=lambda l: (-letter_rates.get(l, 0.0), l)
        )
        letters_str = " ".join(distinct_sorted)
        rows.append(
            f"  <tr>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(word)}</td>'
            f'<td class="freq-letters">{escape(letters_str)}</td>'
            f'<td class="freq-score" data-value="{score:.6f}">{score:.4f}</td>'
            f"</tr>"
        )
    return (
        '<table class="freq-table sortable-table ranking-table">\n'
        + _ranking_thead(["Rank", "Word", "Distinct letters", "Score"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def render_bigram_ranking(
    words_10: list[str],
    bigram_rates: dict[str, float],
    top_n: int = 50,
) -> str:
    """Top-N ten-letter words by bigram_score, with top-3-contributing-bigrams transparency.

    Columns: Rank | Word | Top contributors | Score.
    'Top contributors' lists the 3 bigrams that contribute most to the word's
    score, where contribution = bigram_rate * count_of_that_bigram_in_word.
    For a word like 'statistics' where 'st' appears 3 times, 'st' is listed
    once with the multiplied contribution.
    """
    score_fn = lambda word: bigram_score(word, bigram_rates)
    ranked = top_n_by_score(words_10, score_fn, n=top_n)
    rows: list[str] = []
    for rank, (word, score) in enumerate(ranked, start=1):
        # Per-word bigram occurrence count
        per_word_bigrams = _Counter(word[i : i + 2] for i in range(len(word) - 1))
        contribs = sorted(
            (
                (bg, bigram_rates.get(bg, 0.0) * cnt)
                for bg, cnt in per_word_bigrams.items()
            ),
            key=lambda kv: (-kv[1], kv[0]),
        )[:3]
        contrib_str = ", ".join(bg for bg, _ in contribs)
        rows.append(
            f"  <tr>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(word)}</td>'
            f'<td class="freq-letters">{escape(contrib_str)}</td>'
            f'<td class="freq-score" data-value="{score:.6f}">{score:.4f}</td>'
            f"</tr>"
        )
    return (
        '<table class="freq-table sortable-table ranking-table">\n'
        + _ranking_thead(["Rank", "Word", "Top contributors", "Score"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def render_trigram_ranking(
    words_10: list[str],
    start_rates: dict[str, float],
    end_rates: dict[str, float],
    top_n: int = 50,
) -> str:
    """Top-N ten-letter words by trigram_score (start + end).

    Columns: Rank | Word | Start | End | Score.
    """
    def score_fn(w: str) -> float:
        return trigram_score(w, start_rates, end_rates)

    ranked = top_n_by_score(words_10, score_fn, n=top_n)
    rows: list[str] = []
    for rank, (word, score) in enumerate(ranked, start=1):
        rows.append(
            f"  <tr>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(word)}</td>'
            f'<td class="freq-letters">{escape(word[:3])}</td>'
            f'<td class="freq-letters">{escape(word[-3:])}</td>'
            f'<td class="freq-score" data-value="{score:.6f}">{score:.4f}</td>'
            f"</tr>"
        )
    return (
        '<table class="freq-table sortable-table ranking-table">\n'
        + _ranking_thead(["Rank", "Word", "Start", "End", "Score"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def render_positional_ranking(
    words_10: list[str],
    first_rates: dict[str, float],
    last_rates: dict[str, float],
    top_n: int = 50,
) -> str:
    """Top-N ten-letter words by positional_endpoint_score (first + last).

    Columns: Rank | Word | First | Last | Score.
    Per DR8: both terms count even when first == last.
    """
    def score_fn(w: str) -> float:
        return positional_endpoint_score(w, first_rates, last_rates)

    ranked = top_n_by_score(words_10, score_fn, n=top_n)
    rows: list[str] = []
    for rank, (word, score) in enumerate(ranked, start=1):
        rows.append(
            f"  <tr>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(word)}</td>'
            f'<td class="freq-letters">{escape(word[0])}</td>'
            f'<td class="freq-letters">{escape(word[-1])}</td>'
            f'<td class="freq-score" data-value="{score:.6f}">{score:.4f}</td>'
            f"</tr>"
        )
    return (
        '<table class="freq-table sortable-table ranking-table">\n'
        + _ranking_thead(["Rank", "Word", "First", "Last", "Score"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )
```

**Implementation notes:**
- `_ranking_thead` is a tiny shared helper for the four ranking tables' thead. `_bar_cell` (Phase 4) is not used in rankings — bars don't add value when the score is already shown numerically.
- All four renderers bind their rate dicts via `lambda` for consistency. `top_n_by_score` expects a 1-arg callable `score_fn(word) -> float`; lambdas are the simplest unambiguous adapter when the underlying scoring function takes more than one argument.
- `data-value` on the score column uses 6 decimal places of precision so the sort works reliably for very close scores; the visible text uses 4 decimal places.
- `ranking-table` is a new class added alongside `freq-table` and `sortable-table`. No new CSS rule required for Phase 5; the existing `.freq-table` styling is sufficient. (If the rankings end up looking too dense, a Phase 6 polish step can add rules later.)
- The `letter-rates` and `bigram-rates` arguments use the `dict[str, float]` rate dicts from `letterfreq.reference.to_rates(...)`. Per-occurrence rates ensure scores are roughly probability-magnitude across all four metrics.

**No commit yet** — wait for Task 2 to write tests.
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Tests for ranking-table renderers

**Verifies:** ten-letter-page.AC6.1, AC6.2, AC6.3, AC6.4, AC6.5.

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_render_ranking.py`

**Implementation:**

```python
"""Tests for letterfreq.render ranking-table functions.

Verifies row counts, structural HTML, and that transparency columns surface
the correct components.
"""

from __future__ import annotations

import string

from letterfreq.render import (
    render_bigram_ranking,
    render_letter_ranking,
    render_positional_ranking,
    render_trigram_ranking,
)


def _ten_letter_words() -> list[str]:
    """Generate 60 distinct 10-letter words for ranking tests.

    Words vary across all positions so per-word scoring (letter, bigram,
    trigram, positional) gets meaningful variation rather than collapsing
    on identical suffixes.
    """
    pairs: list[str] = []
    letters = string.ascii_lowercase
    for i, l1 in enumerate(letters):
        for j, l2 in enumerate(letters):
            # Build a 10-letter word that varies in start, middle, and end.
            middle = letters[(i + j) % 26 : (i + j) % 26 + 6]
            if len(middle) < 6:
                middle += letters[: 6 - len(middle)]
            pairs.append(l1 + l2 + middle + letters[(i * 7 + j * 11) % 26] + letters[(i * 13 + j * 17) % 26])
            if len(pairs) >= 60:
                return pairs
    return pairs


# ---- Letter ranking -----------------------------------------------------------

# AC6.1
def test_letter_ranking_has_top_50_rows() -> None:
    rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    html = render_letter_ranking(_ten_letter_words(), rates, top_n=50)
    assert html.count("<tr>") == 51  # 1 thead + 50 tbody


def test_letter_ranking_transparency_lists_distinct_letters() -> None:
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    # Word 'aabbccddee' has 5 distinct letters: a, b, c, d, e
    html = render_letter_ranking(["aabbccddee"], rates, top_n=1)
    # Each distinct letter should appear in the transparency cell
    for ch in "abcde":
        assert ch in html


def test_letter_ranking_is_sortable() -> None:
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    html = render_letter_ranking(["abcdefghij"], rates, top_n=1)
    assert 'class="freq-table sortable-table ranking-table"' in html
    assert 'class="sortable"' in html


# ---- Bigram ranking -----------------------------------------------------------

# AC6.2
def test_bigram_ranking_has_top_50_rows() -> None:
    rates = {f"{a}{b}": 0.01 for a in "abcde" for b in "abcde"}
    html = render_bigram_ranking(_ten_letter_words(), rates, top_n=50)
    assert html.count("<tr>") == 51


def test_bigram_ranking_transparency_top_3_by_contribution() -> None:
    """For 'statistics' with high 'st' rate, 'st' should appear in top-3 contributors."""
    rates = {"st": 0.5, "ta": 0.01, "at": 0.01, "ti": 0.05, "is": 0.01, "ic": 0.01, "cs": 0.01}
    # 'statistics' has bigrams: st, ta, at, ti, is, st, ti, ic, cs
    # Contributions: st: 0.5 * 2 = 1.0, ti: 0.05 * 2 = 0.1, is: 0.01 * 1 = 0.01, ...
    # Top 3 by contribution: st, ti, then a tie at 0.01 (alphabetical: at)
    html = render_bigram_ranking(["statistics"], rates, top_n=1)
    # 'st' must be in the top-contributors cell (look for it as a standalone token)
    assert "st" in html


# ---- Trigram ranking ----------------------------------------------------------

# AC6.3
def test_trigram_ranking_has_top_50_rows() -> None:
    start_rates = {f"{a}{b}{c}": 0.01 for a in "abc" for b in "abc" for c in "abc"}
    end_rates = dict(start_rates)
    html = render_trigram_ranking(_ten_letter_words(), start_rates, end_rates, top_n=50)
    assert html.count("<tr>") == 51


def test_trigram_ranking_shows_separate_start_end_columns() -> None:
    html = render_trigram_ranking(["abcdefghij"], {"abc": 0.1}, {"hij": 0.1}, top_n=1)
    assert "Start" in html
    assert "End" in html
    # Both trigrams should appear in cells
    assert "abc" in html
    assert "hij" in html


# ---- Positional ranking -------------------------------------------------------

# AC6.5
def test_positional_ranking_has_top_50_rows() -> None:
    first_rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    last_rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    html = render_positional_ranking(_ten_letter_words(), first_rates, last_rates, top_n=50)
    assert html.count("<tr>") == 51


def test_positional_ranking_shows_separate_first_last_columns() -> None:
    html = render_positional_ranking(
        ["abcdefghij"], {"a": 0.1}, {"j": 0.2}, top_n=1
    )
    assert "First" in html
    assert "Last" in html


def test_positional_ranking_doubled_endpoint_word() -> None:
    """A word where w[0] == w[-1] should still get both contributions."""
    first_rates = {"a": 0.5}
    last_rates = {"a": 0.3}
    html = render_positional_ranking(["aaaaaaaaaa"], first_rates, last_rates, top_n=1)
    # Score should be 0.5 + 0.3 = 0.8, rendered as 0.8000
    assert "0.8000" in html


# ---- AC6.4: All ranking tables sortable ---------------------------------------

def test_all_ranking_tables_have_sortable_class() -> None:
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    bigram_rates = {f"{a}{b}": 0.01 for a in "abcd" for b in "abcd"}
    start_rates = {"abc": 0.1}
    end_rates = {"hij": 0.1}
    words = ["abcdefghij"]
    htmls = [
        render_letter_ranking(words, rates, top_n=1),
        render_bigram_ranking(words, bigram_rates, top_n=1),
        render_trigram_ranking(words, start_rates, end_rates, top_n=1),
        render_positional_ranking(words, {"a": 0.1}, {"j": 0.1}, top_n=1),
    ]
    for html in htmls:
        assert 'class="sortable"' in html
```

**Verification:**

```bash
uv run pytest tests/test_render_ranking.py -v
```

Expected: 11 tests pass.

Run full suite:

```bash
uv run pytest -q
```

Expected: all tests pass (cumulative: test_frequencies, test_reference, test_scoring, test_render_reference, test_render_ranking).

**Commit (combined with Task 1):**

```bash
git add letterfreq/render.py tests/test_render_ranking.py
git commit -m "feat: letterfreq.render — ranking-table renderers with transparency, with tests"
```
<!-- END_TASK_2 -->
<!-- END_SUBCOMPONENT_A -->
