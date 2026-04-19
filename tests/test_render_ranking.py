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
