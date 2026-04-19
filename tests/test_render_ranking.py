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


def test_letter_ranking_transparency_lists_distinct_letters_sorted_by_rate() -> None:
    # Non-uniform rates so ordering can be verified, not just presence.
    # Expected order in transparency cell: a (0.5), b (0.3), c (0.1), d (0.05), e (0.02).
    rates = {ch: 0.001 for ch in string.ascii_lowercase}
    rates.update({"a": 0.5, "b": 0.3, "c": 0.1, "d": 0.05, "e": 0.02})
    html = render_letter_ranking(["aabbccddee"], rates, top_n=1)
    # Distinct letters of 'aabbccddee' are {a,b,c,d,e} — joined with spaces,
    # sorted by (-rate, letter) so the cell reads "a b c d e".
    assert "a b c d e" in html


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
    """Transparency sort is by contribution (rate × per-word-count), NOT raw rate.

    Word 'ababababcd' has bigrams: ab (4x), ba (3x), bc (1x), cd (1x).
    Rates: ab=0.1, ba=0.0, bc=0.0, cd=0.25.
    Contributions: ab=0.4, cd=0.25, ba=0.0, bc=0.0.
    Raw-rate ordering would put cd before ab; contribution ordering puts ab first.
    If the implementation were sorting by raw rate, 'cd, ab' would appear in the cell.
    """
    rates = {"ab": 0.1, "ba": 0.0, "bc": 0.0, "cd": 0.25}
    html = render_bigram_ranking(["ababababcd"], rates, top_n=1)
    # Correct contribution ordering: "ab" comes before "cd"
    assert "ab, cd" in html
    # Negative assertion: the raw-rate ordering must NOT appear
    assert "cd, ab" not in html


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
    letter_rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    first_rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    last_rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    html = render_positional_ranking(
        _ten_letter_words(), letter_rates, first_rates, last_rates, top_n=50
    )
    assert html.count("<tr>") == 51


def test_positional_ranking_shows_separate_first_last_columns() -> None:
    letter_rates = {ch: 0.1 for ch in string.ascii_lowercase}
    html = render_positional_ranking(
        ["abcdefghij"], letter_rates, {"a": 0.1}, {"j": 0.2}, top_n=1
    )
    assert "First" in html
    assert "Last" in html


def test_positional_ranking_doubled_endpoint_word() -> None:
    """A word where w[0] == w[-1] still receives both positional bonuses."""
    letter_rates = {"a": 1.0}
    first_rates = {"a": 0.5}
    last_rates = {"a": 0.3}
    html = render_positional_ranking(
        ["aaaaaaaaaa"], letter_rates, first_rates, last_rates, top_n=1
    )
    # Score = letter_score('aaaa...')=1.0 + first['a']=0.5 + last['a']=0.3 = 1.8
    assert "1.8000" in html


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
        render_positional_ranking(words, rates, {"a": 0.1}, {"j": 0.1}, top_n=1),
    ]
    for html in htmls:
        assert 'class="sortable"' in html
