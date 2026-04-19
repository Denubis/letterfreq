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
