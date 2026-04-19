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


def test_bigram_score_distinct_cap_on_repeats() -> None:
    rates = {"st": 0.1, "ta": 0.05, "at": 0.05, "ti": 0.05, "is": 0.05, "ic": 0.05, "cs": 0.05}
    # 'statistics' has bigrams: st, ta, at, ti, is, st, ti, ic, cs
    # Distinct set is {st, ta, at, ti, is, ic, cs} — 7 rates, each counted once.
    expected = 0.1 + 0.05 + 0.05 + 0.05 + 0.05 + 0.05 + 0.05
    assert bigram_score("statistics", rates) == pytest.approx(expected)


def test_bigram_score_uniform_rates_all_distinct_bigrams() -> None:
    rates = two_letter_bigram_rates(0.05)
    # 'abcdefghij' has 9 consecutive, all distinct → 9 * 0.05 = 0.45
    assert bigram_score("abcdefghij", rates) == pytest.approx(9 * 0.05)


def test_bigram_score_single_repeated_bigram_counted_once() -> None:
    # 'ababababab' has only one distinct bigram ('ab' + 'ba' alternating), so {ab, ba}.
    rates = {"ab": 0.1, "ba": 0.2}
    assert bigram_score("ababababab", rates) == pytest.approx(0.3)


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
def test_positional_endpoint_score_coverage_plus_endpoints() -> None:
    letter_rates = alpha_rates(0.1)
    first_rates = {"a": 0.5, "b": 0.05}
    last_rates = {"j": 0.3, "k": 0.05}
    # 'abcdefghij' has 10 distinct letters → letter_score = 1.0
    # + first['a']=0.5 + last['j']=0.3 = 1.8
    assert positional_endpoint_score(
        "abcdefghij", letter_rates, first_rates, last_rates
    ) == pytest.approx(1.8)


# AC3.6
def test_positional_endpoint_score_no_cap_when_endpoints_equal() -> None:
    letter_rates = {"a": 1.0}
    first_rates = {"a": 0.1}
    last_rates = {"a": 0.2}
    # letter_score('aaaaaaaaaa') = 1.0 (distinct cap → only 'a' counts once)
    # Positional bonuses add 0.1 + 0.2, both apply even when word[0] == word[-1].
    assert positional_endpoint_score(
        "aaaaaaaaaa", letter_rates, first_rates, last_rates
    ) == pytest.approx(1.3)


def test_positional_endpoint_score_unknown_letter_treated_as_zero() -> None:
    assert positional_endpoint_score("aaaaaaaaaa", {}, {}, {}) == pytest.approx(0.0)


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


# ---- Runtime contract guards (proleptic-fix regression tests) -----------------


def test_trigram_score_rejects_short_word() -> None:
    with pytest.raises(ValueError, match="len\\(word\\) >= 3"):
        trigram_score("ab", {}, {})


def test_positional_endpoint_score_rejects_empty_word() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        positional_endpoint_score("", {}, {}, {})


def test_top_n_by_score_rejects_nan_score() -> None:
    def nan_score(_: str) -> float:
        return float("nan")

    with pytest.raises(ValueError, match="non-finite"):
        top_n_by_score(["foo", "bar"], nan_score, n=10)


def test_top_n_by_score_rejects_inf_score() -> None:
    def inf_score(_: str) -> float:
        return float("inf")

    with pytest.raises(ValueError, match="non-finite"):
        top_n_by_score(["foo"], inf_score, n=10)
