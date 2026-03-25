"""Tests for overall letter frequency computation (AC2.1)."""

from __future__ import annotations

import string

from main import compute_overall_frequencies


def test_frequency_sum_equals_five_times_word_count(words):
    """AC2.1: Sum of all letter counts must equal 5 * word_count."""
    freq = compute_overall_frequencies(words)
    total = freq["len"].sum()
    assert total == 5 * len(words), (
        f"Expected {5 * len(words)}, got {total}"
    )


def test_all_26_letters_present(words):
    """Every lowercase letter should appear at least once in five-letter words."""
    freq = compute_overall_frequencies(words)
    letters_in_freq = set(freq["letter"].to_list())
    assert letters_in_freq == set(string.ascii_lowercase), (
        f"Missing letters: {set(string.ascii_lowercase) - letters_in_freq}"
    )


def test_spot_check_letter_e(words):
    """Spot-check: count of 'e' should match manual count across filtered words."""
    freq = compute_overall_frequencies(words)

    # Manual count of 'e' across all words
    manual_count = sum(w.count("e") for w in words)

    e_row = freq.filter(freq["letter"] == "e")
    assert len(e_row) == 1, "Expected exactly one row for 'e'"
    polars_count = e_row["len"].item()
    assert polars_count == manual_count, (
        f"Polars count for 'e': {polars_count}, manual: {manual_count}"
    )


def test_word_count_is_positive(words):
    """Sanity check: we should have a meaningful number of words."""
    assert len(words) > 1000, f"Expected >1000 words, got {len(words)}"


def test_all_words_are_five_letters(words):
    """Every loaded word should be exactly 5 lowercase letters."""
    for w in words:
        assert len(w) == 5, f"Word {w!r} is not 5 characters"
        assert w.isalpha() and w.islower(), f"Word {w!r} is not lowercase alpha"
