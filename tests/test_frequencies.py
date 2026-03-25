"""Tests for overall letter frequency computation (AC2.1)."""

from __future__ import annotations

import string

import pytest

from main import compute_bigrams, compute_overall_frequencies, compute_positional_unigrams


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


# --- Positional unigram tests ---


def test_positional_unigram_column_sums(words):
    """AC2.2: For each position, the sum of all 26 letter counts equals word_count."""
    unigrams = compute_positional_unigrams(words)
    word_count = len(words)
    for pos in range(5):
        total = sum(unigrams[letter][pos] for letter in string.ascii_lowercase)
        assert total == word_count, (
            f"Position {pos + 1}: sum {total} != word_count {word_count}"
        )


def test_positional_unigram_all_26_letters(words):
    """All 26 lowercase letters should have entries in the unigram dict."""
    unigrams = compute_positional_unigrams(words)
    assert set(unigrams.keys()) == set(string.ascii_lowercase), (
        f"Missing letters: {set(string.ascii_lowercase) - set(unigrams.keys())}"
    )


def test_positional_unigram_spot_check_e_pos5(words):
    """Spot-check: count of 'e' at position 5 matches manual count."""
    unigrams = compute_positional_unigrams(words)
    manual_count = sum(1 for w in words if w[4] == "e")
    assert unigrams["e"][4] == manual_count, (
        f"'e' at pos 5: polars={unigrams['e'][4]}, manual={manual_count}"
    )


# --- Bigram tests ---


@pytest.mark.parametrize("pair", ["1_2", "2_3", "3_4", "4_5"])
def test_bigram_position_sum(words, pair):
    """AC2.3: Sum of all bigram counts at each position pair equals word_count."""
    bigrams = compute_bigrams(words)
    total = sum(
        count
        for seconds in bigrams[pair].values()
        for count in seconds.values()
    )
    assert total == len(words), f"Pair {pair}: expected {len(words)}, got {total}"


def test_bigram_spot_check_th(words):
    """Spot-check: count of words starting with 'th' matches bigrams['1_2']['t']['h']."""
    bigrams = compute_bigrams(words)
    manual_count = sum(1 for w in words if w[:2] == "th")
    polars_count = bigrams["1_2"].get("t", {}).get("h", 0)
    assert polars_count == manual_count, (
        f"bigrams['1_2']['t']['h']: polars={polars_count}, manual={manual_count}"
    )
