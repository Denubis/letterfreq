"""Tests for overall letter frequency computation (AC2.1)."""

from __future__ import annotations

import string

import pytest

from main import (
    compute_bigrams,
    compute_overall_frequencies,
    compute_positional_unigrams,
    get_neighbour_distributions,
)


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


# --- Neighbour distribution / drill-down tests ---


@pytest.fixture(scope="session")
def bigrams(words):
    return compute_bigrams(words)


def test_neighbour_middle_position_has_both(words, bigrams):
    """For letter 'e' at position 3, both left and right neighbours are returned."""
    result = get_neighbour_distributions(bigrams, "e", 3)
    assert "left" in result, "Expected 'left' key for middle position"
    assert "right" in result, "Expected 'right' key for middle position"
    assert len(result["left"]) > 0, "Left neighbour distribution should be non-empty"
    assert len(result["right"]) > 0, "Right neighbour distribution should be non-empty"


def test_neighbour_position_1_only_right(words, bigrams):
    """For any letter at position 1, only right neighbour is returned."""
    result = get_neighbour_distributions(bigrams, "s", 1)
    assert "left" not in result, "Position 1 should not have left neighbour"
    assert "right" in result, "Position 1 should have right neighbour"


def test_neighbour_position_5_only_left(words, bigrams):
    """For any letter at position 5, only left neighbour is returned."""
    result = get_neighbour_distributions(bigrams, "s", 5)
    assert "right" not in result, "Position 5 should not have right neighbour"
    assert "left" in result, "Position 5 should have left neighbour"


def test_neighbour_sum_matches_unigram(words, bigrams):
    """Sum of right- and left-neighbour counts for letter X at position N equals unigram count."""
    unigrams = compute_positional_unigrams(words)
    # Test several letter/position combos
    for letter in ["e", "s", "t", "a"]:
        for pos in range(1, 5):  # positions 1-4 have right neighbours
            result = get_neighbour_distributions(bigrams, letter, pos)
            right_sum = sum(result["right"].values())
            unigram_count = unigrams[letter][pos - 1]  # 0-indexed
            assert right_sum == unigram_count, (
                f"Right-neighbour sum for '{letter}' at pos {pos}: "
                f"{right_sum} != unigram {unigram_count}"
            )
    for letter in ["e", "s", "a"]:
        for pos in range(2, 6):  # positions 2-5 have left neighbours
            result = get_neighbour_distributions(bigrams, letter, pos)
            left_sum = sum(result["left"].values())
            unigram_count = unigrams[letter][pos - 1]  # 0-indexed
            assert left_sum == unigram_count, (
                f"Left-neighbour sum for '{letter}' at pos {pos}: "
                f"{left_sum} != unigram {unigram_count}"
            )
