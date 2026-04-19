# Ten-Letter Page Implementation Plan — Phase 3: `letterfreq` package — scoring module

**Goal:** Implement the four ten-letter scoring functions (`letter_score`, `bigram_score`, `trigram_score`, `positional_endpoint_score`) and a generic `top_n_by_score` helper. All pure, parameterised on baseline rate dicts produced by Phase 2.

**Architecture:** Pure functional core. Each scoring function takes `(word, *rates_dicts)` and returns a `float`. `top_n_by_score` takes an iterable of words and a `score_fn` callable and returns the top-N as `[(word, score), ...]`, sorted descending with alphabetical tie-break for stability.

**Tech Stack:** Python 3.14+, pytest. No new dependencies.

**Scope:** Phase 3 of 7 from `/home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md`.

**Codebase verified:** 2026-04-19. `letterfreq/__init__.py` and `letterfreq/reference.py` will exist after Phase 2 commits. No `letterfreq/scoring.py` yet. Existing test patterns (pytest, hand-checked tiny inputs) established in Phase 2.

**Phase Type:** functionality

---

## Acceptance Criteria Coverage

This phase implements and tests:

### ten-letter-page.AC3: Scoring formulas
- **ten-letter-page.AC3.1 Success:** `letter_score("aaaaaaaaaa", {a:0.1, ...})` returns 0.1 (distinct-only cap).
- **ten-letter-page.AC3.2 Success:** `letter_score("abcdefghij", rates)` returns `sum(rates[l] for l in "abcdefghij")`.
- **ten-letter-page.AC3.3 Success:** `bigram_score` on a 10-letter word with controlled rates returns the sum of the 9 consecutive-bigram rates.
- **ten-letter-page.AC3.4 Success:** `trigram_score("abcdefghij", start_rates, end_rates)` returns `start_rates["abc"] + end_rates["hij"]`.
- **ten-letter-page.AC3.5 Success:** `positional_endpoint_score("abcdefghij", first_rates, last_rates)` returns `first_rates["a"] + last_rates["j"]`.
- **ten-letter-page.AC3.6 Success:** `positional_endpoint_score("aaaaaaaaaa", first_rates, last_rates)` returns `first_rates["a"] + last_rates["a"]` (no distinct cap).

### ten-letter-page.AC4: Ranking ordering and tie-break
- **ten-letter-page.AC4.1 Success:** Two words with identical scores are returned in alphabetical order.
- **ten-letter-page.AC4.2 Success:** `top_n_by_score` returns exactly `n` entries when ≥`n` candidates exist.
- **ten-letter-page.AC4.3 Success:** Rank-1 entry has the highest score among all candidates.

---

## Implementation Tasks

<!-- START_SUBCOMPONENT_A (tasks 1-2) -->
<!-- START_TASK_1 -->
### Task 1: Implement `letterfreq/scoring.py`

**Verifies (when paired with Task 2 tests):** ten-letter-page.AC3.1, AC3.2, AC3.3, AC3.4, AC3.5, AC3.6, AC4.1, AC4.2, AC4.3.

**Files:**
- Create: `/home/brian/llm/letterfreq/letterfreq/scoring.py`

**Implementation:**

```python
"""Per-word scoring functions for ranking ten-letter words.

Each scoring function takes a word and one or more baseline rate dicts and
returns a float. All functions are pure and side-effect-free. They handle
absent letters/bigrams/trigrams by treating their rate as 0 (via dict.get).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable


# ---- Scoring functions --------------------------------------------------------


def letter_score(word: str, letter_rates: dict[str, float]) -> float:
    """Sum baseline letter rates over the DISTINCT letters in `word`.

    Per DR2: repeated letters do not increase the score (hard cap at first
    occurrence). 'aaaaa' scores `letter_rates['a']`, not `5 * letter_rates['a']`.
    """
    return sum(letter_rates.get(letter, 0.0) for letter in set(word))


def bigram_score(word: str, bigram_rates: dict[str, float]) -> float:
    """Sum baseline bigram rates over each of the consecutive bigrams in `word`.

    Includes repeats: if a bigram appears multiple times in `word`, its rate
    is added that many times. (Distinct from letter_score's distinct cap.)
    """
    return sum(
        bigram_rates.get(word[i : i + 2], 0.0) for i in range(len(word) - 1)
    )


def trigram_score(
    word: str,
    start_rates: dict[str, float],
    end_rates: dict[str, float],
) -> float:
    """Sum the start-trigram rate and the end-trigram rate of `word`.

    Returns `start_rates[word[:3]] + end_rates[word[-3:]]`. Both terms are 0
    if the trigram is absent from its respective rate dict.

    Assumes len(word) >= 3.
    """
    return start_rates.get(word[:3], 0.0) + end_rates.get(word[-3:], 0.0)


def positional_endpoint_score(
    word: str,
    first_rates: dict[str, float],
    last_rates: dict[str, float],
) -> float:
    """Sum the first-letter rate and the last-letter rate of `word`.

    Per DR8: both terms contribute even when `word[0] == word[-1]` (no distinct
    cap, distinguishing this score from `letter_score`).

    Assumes len(word) >= 1.
    """
    return first_rates.get(word[0], 0.0) + last_rates.get(word[-1], 0.0)


# ---- Generic top-N helper -----------------------------------------------------


def top_n_by_score(
    words: Iterable[str],
    score_fn: Callable[[str], float],
    n: int = 50,
) -> list[tuple[str, float]]:
    """Return the top-N (word, score) tuples, sorted descending by score.

    Tie-break: alphabetical by word (stable). The returned list has at most
    `n` entries; fewer if `words` has fewer than `n` distinct entries.

    `score_fn` must be a callable taking a single `word` argument and returning
    a float. Use `functools.partial` to bind baseline rate dicts:

        from functools import partial
        score = partial(letter_score, letter_rates=rates)
        top = top_n_by_score(words_10, score, n=50)
    """
    scored = [(word, score_fn(word)) for word in words]
    # Sort by (-score, word): higher score first, ties broken alphabetically.
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored[:n]
```

**Implementation notes:**
- All scoring functions use `dict.get(key, 0.0)` so absent baseline entries don't raise KeyError — important for words containing letters/bigrams/trigrams that may legitimately not appear in the baseline (rare for the reasonably large 3–10 corpus, but defensive).
- `letter_score` uses `set(word)` to dedupe before summing. For a 10-letter word this is at most 10 elements; cost is negligible.
- `top_n_by_score` sorts by `(-score, word)`: Python's tuple comparison gives descending score with ascending alphabetical tie-break in one pass. No separate stable sort needed.
- `score_fn` is a free callable, allowing the caller to bind any combination of rate dicts via `functools.partial` or a lambda.

**No commit yet** — wait for Task 2 to write tests.
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Tests for `letterfreq/scoring.py`

**Verifies:** ten-letter-page.AC3.1, AC3.2, AC3.3, AC3.4, AC3.5, AC3.6, AC4.1, AC4.2, AC4.3.

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_scoring.py`

**Implementation:**

```python
"""Tests for letterfreq.scoring."""

from __future__ import annotations

from functools import partial

import pytest

from letterfreq.scoring import (
    bigram_score,
    letter_score,
    positional_endpoint_score,
    top_n_by_score,
    trigram_score,
)


# ---- Controlled rate dicts -----------------------------------------------------


def alpha_rates(value: float = 0.1) -> dict[str, float]:
    """Uniform rate per letter — all 26 letters get `value`."""
    return {chr(ord("a") + i): value for i in range(26)}


def two_letter_bigram_rates(value: float = 0.05) -> dict[str, float]:
    """Uniform rate for every two-letter combination of a–z."""
    rates: dict[str, float] = {}
    for i in range(26):
        for j in range(26):
            rates[chr(ord("a") + i) + chr(ord("a") + j)] = value
    return rates


# ---- letter_score -------------------------------------------------------------

# AC3.1
def test_letter_score_distinct_cap_all_same_letter() -> None:
    rates = alpha_rates(0.1)
    assert letter_score("aaaaaaaaaa", rates) == pytest.approx(0.1)


# AC3.2
def test_letter_score_ten_distinct_letters() -> None:
    rates = alpha_rates(0.1)
    expected = sum(rates[letter] for letter in "abcdefghij")
    assert letter_score("abcdefghij", rates) == pytest.approx(expected)


def test_letter_score_with_repeats_uses_distinct_cap() -> None:
    rates = alpha_rates(0.1)
    # 'banana' has 3 distinct letters: b, a, n
    assert letter_score("banana", rates) == pytest.approx(0.3)


def test_letter_score_unknown_letter_treated_as_zero() -> None:
    rates = {"a": 0.5}
    # 'b' and 'c' not in rates, treated as 0.0
    assert letter_score("abc", rates) == pytest.approx(0.5)


# ---- bigram_score -------------------------------------------------------------

# AC3.3
def test_bigram_score_uniform_rates_ten_letter_word() -> None:
    rates = two_letter_bigram_rates(0.05)
    # 10-letter word has 9 consecutive bigrams; uniform 0.05 each => 0.45
    assert bigram_score("abcdefghij", rates) == pytest.approx(9 * 0.05)


def test_bigram_score_handcheck_specific_pairs() -> None:
    rates = {"ab": 0.1, "bc": 0.2, "cd": 0.3}
    assert bigram_score("abcd", rates) == pytest.approx(0.1 + 0.2 + 0.3)


def test_bigram_score_repeated_bigram_counted_each_time() -> None:
    rates = {"st": 0.1, "ta": 0.05, "at": 0.05, "ti": 0.05, "is": 0.05, "ic": 0.05, "cs": 0.05}
    # 'statistics' has bigrams: st, ta, at, ti, is, st, ti, ic, cs
    # st appears twice, ti appears twice — both counted twice
    expected = 0.1 + 0.05 + 0.05 + 0.05 + 0.05 + 0.1 + 0.05 + 0.05 + 0.05
    assert bigram_score("statistics", rates) == pytest.approx(expected)


# ---- trigram_score ------------------------------------------------------------

# AC3.4
def test_trigram_score_handcheck() -> None:
    start_rates = {"abc": 0.2, "xyz": 0.1}
    end_rates = {"hij": 0.3, "uvw": 0.05}
    assert trigram_score("abcdefghij", start_rates, end_rates) == pytest.approx(0.5)


def test_trigram_score_unknown_trigram_treated_as_zero() -> None:
    assert trigram_score("zzzzzzzzzz", {}, {}) == pytest.approx(0.0)


# ---- positional_endpoint_score ------------------------------------------------

# AC3.5
def test_positional_endpoint_score_distinct_endpoints() -> None:
    first_rates = {"a": 0.1, "b": 0.05}
    last_rates = {"j": 0.2, "k": 0.05}
    assert positional_endpoint_score("abcdefghij", first_rates, last_rates) == pytest.approx(0.3)


# AC3.6
def test_positional_endpoint_score_no_distinct_cap_when_endpoints_equal() -> None:
    first_rates = {"a": 0.1}
    last_rates = {"a": 0.2}
    # Both terms contribute even though word[0] == word[-1]
    assert positional_endpoint_score("aaaaaaaaaa", first_rates, last_rates) == pytest.approx(0.3)


def test_positional_endpoint_score_unknown_letter_treated_as_zero() -> None:
    assert positional_endpoint_score("aaaaaaaaaa", {}, {}) == pytest.approx(0.0)


# ---- top_n_by_score -----------------------------------------------------------

# AC4.1
def test_top_n_by_score_alphabetical_tiebreak() -> None:
    rates = alpha_rates(0.1)
    # All three words have the same set of distinct letters {a,b,c} → score 0.3
    score = partial(letter_score, letter_rates=rates)
    result = top_n_by_score(["cba", "abc", "bca"], score, n=3)
    assert [w for w, _ in result] == ["abc", "bca", "cba"]


# AC4.2
def test_top_n_by_score_returns_exactly_n() -> None:
    rates = alpha_rates(0.1)
    score = partial(letter_score, letter_rates=rates)
    words = [chr(ord("a") + i) * 5 for i in range(20)]  # 20 single-letter-repeated words
    result = top_n_by_score(words, score, n=10)
    assert len(result) == 10


def test_top_n_by_score_returns_all_when_fewer_than_n() -> None:
    rates = alpha_rates(0.1)
    score = partial(letter_score, letter_rates=rates)
    result = top_n_by_score(["a", "b", "c"], score, n=10)
    assert len(result) == 3


# AC4.3
def test_top_n_by_score_rank_one_has_highest_score() -> None:
    # Construct words with controllable scores
    rates = {"a": 1.0, "b": 0.5, "c": 0.1}
    score = partial(letter_score, letter_rates=rates)
    result = top_n_by_score(["bbb", "aaa", "ccc"], score, n=3)
    assert result[0][0] == "aaa"  # highest score (1.0)
    assert result[0][1] == pytest.approx(1.0)
```

**Verification:**

```bash
uv run pytest tests/test_scoring.py -v
```

Expected: all 16 tests pass.

Run full test suite to confirm no regression:

```bash
uv run pytest -q
```

Expected: existing `test_frequencies.py` and `test_reference.py` tests plus the new `test_scoring.py` tests all pass.

**Commit (combined with Task 1):**

```bash
git add letterfreq/scoring.py tests/test_scoring.py
git commit -m "feat: letterfreq.scoring — four scoring functions and top_n helper, with tests"
```
<!-- END_TASK_2 -->
<!-- END_SUBCOMPONENT_A -->
