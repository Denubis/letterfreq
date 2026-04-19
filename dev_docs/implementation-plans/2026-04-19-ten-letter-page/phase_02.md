# Ten-Letter Page Implementation Plan — Phase 2: `letterfreq` package — reference frequency module

**Goal:** Establish the `letterfreq/` Python package and implement pure functional baseline-frequency counting (letter, bigram, start trigram, end trigram, first letter, last letter) plus a `to_rates` helper.

**Architecture:** Pure functional core (FCIS). All functions take an iterable of words and return plain `dict[str, int]` counts (or `dict[str, float]` rates). No I/O, no globals, no caching, no side effects. Existing `main.py` functions (used by the five-letter page) are NOT moved — they stay where they are. The new package is additive.

**Tech Stack:** Python 3.14+, pytest >= 9.0.2 (existing). No new dependencies.

**Scope:** Phase 2 of 7 from `/home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md`.

**Codebase verified:** 2026-04-19. Key findings relevant to this phase:
- No `letterfreq/` directory exists.
- `tests/conftest.py` provides session-scoped `words` and `word_count` fixtures sourced from `main.py::load_words` (read `data/words.txt`). These fixtures are five-letter-specific and should NOT be reused for ten-letter tests; this phase's tests use small hand-crafted inputs and a separate fixture if needed for the baseline corpus.
- Existing `tests/test_frequencies.py` imports `compute_overall_frequencies, compute_positional_unigrams, compute_bigrams, compute_trigrams, get_neighbour_distributions` from `main.py`. Untouched by this phase.

**Phase Type:** functionality

---

## Acceptance Criteria Coverage

This phase implements and tests:

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

### ten-letter-page.AC10: Baseline first-letter and last-letter frequencies are correct
- **ten-letter-page.AC10.1 Success:** `first_letter_counts(["cation", "static"])` returns `{c:1, s:1}`.
- **ten-letter-page.AC10.2 Success:** `last_letter_counts(["cation", "static"])` returns `{n:1, c:1}`.
- **ten-letter-page.AC10.3 Success:** A 3-letter word `"cat"` contributes `{c:1}` to first-letter counts and `{t:1}` to last-letter counts (no minimum-length filter — every word in the baseline contributes).
- **ten-letter-page.AC10.4 Success:** `first_letter_counts` and `last_letter_counts` on the actual `words_3_to_10.txt` corpus produce non-zero counts for at least the common starting/ending letters (e.g., 's' present in both, 'e' present as last-letter).

---

## Implementation Tasks

<!-- START_TASK_1 -->
### Task 1: Create `letterfreq/__init__.py` (package marker)

**Files:**
- Create: `/home/brian/llm/letterfreq/letterfreq/__init__.py`

**Implementation:**

```python
"""Pure-functional building blocks for the ten-letter analysis page.

Modules:
    reference: Baseline frequency counters for letter, bigram, start/end trigram,
               and first/last letter over an arbitrary word corpus.
    scoring:   Per-word scoring functions for ranking ten-letter words.
    render:    HTML rendering helpers for the reference and ranking tables.

Each module is side-effect-free; entry scripts (`main.py`, `main_ten.py`)
do I/O and call into these modules.
"""
```

**Verification:**

```bash
uv run python -c "import letterfreq; print(letterfreq.__doc__.splitlines()[0])"
```

Expected: prints `Pure-functional building blocks for the ten-letter analysis page.`

**No commit** — combined with Task 2 commit.
<!-- END_TASK_1 -->

<!-- START_SUBCOMPONENT_A (tasks 2-3) -->
<!-- START_TASK_2 -->
### Task 2: Implement `letterfreq/reference.py`

**Verifies (when paired with Task 3 tests):** ten-letter-page.AC1.1, AC1.2, AC1.3, AC2.1, AC2.2, AC2.3, AC2.4, AC10.1, AC10.2, AC10.3.

**Files:**
- Create: `/home/brian/llm/letterfreq/letterfreq/reference.py`

**Implementation:**

```python
"""Baseline frequency counters over an arbitrary word corpus.

All functions are pure: input is an iterable of pre-cleaned lowercase words
(no validation here — the caller is responsible for filtering); output is a
plain dict. No I/O, no globals.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


def letter_counts(words: Iterable[str]) -> dict[str, int]:
    """Count occurrences of each letter across all words."""
    counter: Counter[str] = Counter()
    for word in words:
        counter.update(word)
    return dict(counter)


def bigram_counts(words: Iterable[str]) -> dict[str, int]:
    """Count consecutive two-letter sequences across all words.

    For each word, every adjacent letter pair contributes one count, including
    repeats (e.g., 'eel' contributes 'ee' and 'el').
    """
    counter: Counter[str] = Counter()
    for word in words:
        for i in range(len(word) - 1):
            counter[word[i : i + 2]] += 1
    return dict(counter)


def start_trigram_counts(
    words: Iterable[str], min_length: int = 4
) -> dict[str, int]:
    """Count the first three letters of each word of length >= min_length.

    Default min_length=4 (per DR3) avoids the 3-letter double-count where a
    3-letter word's start trigram and end trigram are identical.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if len(word) >= min_length:
            counter[word[:3]] += 1
    return dict(counter)


def end_trigram_counts(
    words: Iterable[str], min_length: int = 4
) -> dict[str, int]:
    """Count the last three letters of each word of length >= min_length.

    Default min_length=4 (per DR3) — see start_trigram_counts.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if len(word) >= min_length:
            counter[word[-3:]] += 1
    return dict(counter)


def first_letter_counts(words: Iterable[str]) -> dict[str, int]:
    """Count the first letter of each word.

    No minimum-length filter (per DR8) — every word in the baseline
    contributes its first letter exactly once.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if word:
            counter[word[0]] += 1
    return dict(counter)


def last_letter_counts(words: Iterable[str]) -> dict[str, int]:
    """Count the last letter of each word.

    No minimum-length filter (per DR8) — every word in the baseline
    contributes its last letter exactly once.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if word:
            counter[word[-1]] += 1
    return dict(counter)


def to_rates(counts: dict[str, int], total: int) -> dict[str, float]:
    """Convert raw counts to per-occurrence rates.

    Rates are `count / total`. Caller chooses what `total` means (sum of
    counts, total word count, etc.). Returns 0.0 for any zero count.
    """
    if total <= 0:
        return {key: 0.0 for key in counts}
    return {key: value / total for key, value in counts.items()}
```

**Implementation notes:**
- Empty-string guard in `first_letter_counts` and `last_letter_counts` handles the case where the iterable contains an empty string (defensive — production callers will pre-filter).
- Returns `dict` (not `Counter`) so callers see a stable plain-dict API.
- The pure-Python loop is fast enough for the 250k-word baseline (sub-second on commodity hardware); no need for Polars here.

**No commit yet** — wait for Task 3 to write tests, then commit module + tests together.
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Tests for `letterfreq/reference.py`

**Verifies:** ten-letter-page.AC1.1, AC1.2, AC1.3, AC1.4, AC2.1, AC2.2, AC2.3, AC2.4, AC10.1, AC10.2, AC10.3, AC10.4.

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_reference.py`

**Implementation:**

```python
"""Tests for letterfreq.reference."""

from __future__ import annotations

import string
from pathlib import Path

import pytest

from letterfreq.reference import (
    bigram_counts,
    end_trigram_counts,
    first_letter_counts,
    last_letter_counts,
    letter_counts,
    start_trigram_counts,
    to_rates,
)


# ---- Hand-checked tiny inputs -------------------------------------------------

# AC1.1
def test_letter_counts_handcheck() -> None:
    assert letter_counts(["cat", "act"]) == {"a": 2, "c": 2, "t": 2}


# AC1.2
def test_bigram_counts_handcheck() -> None:
    assert bigram_counts(["cat", "act"]) == {"ca": 1, "at": 1, "ac": 1, "ct": 1}


# AC1.3
def test_to_rates_sums_to_one() -> None:
    rates = to_rates({"a": 2, "c": 2, "t": 2}, total=6)
    assert rates == {"a": pytest.approx(1 / 3), "c": pytest.approx(1 / 3), "t": pytest.approx(1 / 3)}
    assert sum(rates.values()) == pytest.approx(1.0)


def test_to_rates_zero_total_returns_zeros() -> None:
    assert to_rates({"a": 5}, total=0) == {"a": 0.0}


def test_to_rates_trigram_denominator_pattern_sums_to_one() -> None:
    """Regression test for the Phase 6 denominator bug: when counting trigrams
    that skip short words, the correct denominator is `sum(counts.values())`
    (equivalently, the number of words that contributed), NOT `len(all_words)`.

    This test demonstrates the correct pattern so the implementation in
    main_ten.py is unambiguous.
    """
    words = ["cat", "cats", "caste", "castle"]  # mix of length 3, 4, 5, 6
    start = start_trigram_counts(words)  # default min_length=4 skips "cat"
    # Only 3 words contributed: "cats", "caste", "castle"
    assert sum(start.values()) == 3
    # Wrong denominator (len(words)=4) gives rates summing to 3/4
    wrong = to_rates(start, total=len(words))
    assert sum(wrong.values()) == pytest.approx(3 / 4)
    # Correct denominator (sum of counts) gives rates summing to 1.0
    correct = to_rates(start, total=sum(start.values()))
    assert sum(correct.values()) == pytest.approx(1.0)


# AC2.1
def test_start_trigram_handcheck() -> None:
    assert start_trigram_counts(["cation", "static"]) == {"cat": 1, "sta": 1}


# AC2.2
def test_end_trigram_handcheck() -> None:
    assert end_trigram_counts(["cation", "static"]) == {"ion": 1, "tic": 1}


# AC2.3
def test_four_letter_word_distinct_start_and_end_trigrams() -> None:
    assert start_trigram_counts(["cats"]) == {"cat": 1}
    assert end_trigram_counts(["cats"]) == {"ats": 1}


# AC2.4
def test_three_letter_word_excluded_from_trigram_counts() -> None:
    assert start_trigram_counts(["cat"]) == {}
    assert end_trigram_counts(["cat"]) == {}


def test_three_letter_word_included_when_min_length_lowered() -> None:
    assert start_trigram_counts(["cat"], min_length=3) == {"cat": 1}
    assert end_trigram_counts(["cat"], min_length=3) == {"cat": 1}


# AC10.1
def test_first_letter_counts_handcheck() -> None:
    assert first_letter_counts(["cation", "static"]) == {"c": 1, "s": 1}


# AC10.2
def test_last_letter_counts_handcheck() -> None:
    assert last_letter_counts(["cation", "static"]) == {"n": 1, "c": 1}


# AC10.3
def test_three_letter_word_in_first_last_counts() -> None:
    assert first_letter_counts(["cat"]) == {"c": 1}
    assert last_letter_counts(["cat"]) == {"t": 1}


# ---- Integration: real baseline corpus -----------------------------------------

BASELINE_PATH = Path(__file__).parent.parent / "data" / "words_3_to_10.txt"


@pytest.fixture(scope="module")
def baseline_words() -> list[str]:
    if not BASELINE_PATH.exists():
        pytest.skip(f"baseline corpus not present: {BASELINE_PATH}")
    return [w for w in BASELINE_PATH.read_text().splitlines() if w]


# AC1.4
def test_letter_counts_cover_all_alpha(baseline_words: list[str]) -> None:
    counts = letter_counts(baseline_words)
    for letter in string.ascii_lowercase:
        assert counts.get(letter, 0) > 0, f"letter {letter!r} missing from baseline"


def test_bigram_counts_have_common_pairs(baseline_words: list[str]) -> None:
    counts = bigram_counts(baseline_words)
    for pair in ("th", "er", "in", "an", "re"):
        assert counts.get(pair, 0) > 0, f"common bigram {pair!r} missing"


# AC10.4
def test_first_letter_counts_cover_common(baseline_words: list[str]) -> None:
    counts = first_letter_counts(baseline_words)
    for letter in ("s", "p", "c", "a", "b"):
        assert counts.get(letter, 0) > 0


def test_last_letter_counts_cover_common(baseline_words: list[str]) -> None:
    counts = last_letter_counts(baseline_words)
    for letter in ("e", "s", "y", "d", "n"):
        assert counts.get(letter, 0) > 0
```

**Verification:**

```bash
uv run pytest tests/test_reference.py -v
```

Expected: 17 tests pass (13 hand-checked tiny-input tests + 4 baseline-corpus integration tests; the latter will be skipped if `data/words_3_to_10.txt` doesn't exist, but in the normal flow Phase 1 has already produced the file).

Confirm existing tests still pass (no regression in five-letter test suite):

```bash
uv run pytest -q
```

Expected: all tests in both `tests/test_frequencies.py` (existing) and `tests/test_reference.py` (new) pass.

**Commit (combined with Task 1 + Task 2):**

```bash
git add letterfreq/__init__.py letterfreq/reference.py tests/test_reference.py
git commit -m "feat: letterfreq.reference — baseline frequency counters with tests"
```
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->
