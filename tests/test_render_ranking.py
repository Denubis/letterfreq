"""Tests for letterfreq.render ranking-table functions.

Verifies row counts, structural HTML, transparency columns, bucket collapse,
exemplar cascade, and expansion-panel shell emission.
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
            middle = letters[(i + j) % 26 : (i + j) % 26 + 6]
            if len(middle) < 6:
                middle += letters[: 6 - len(middle)]
            pairs.append(l1 + l2 + middle + letters[(i * 7 + j * 11) % 26] + letters[(i * 13 + j * 17) % 26])
            if len(pairs) >= 60:
                return pairs
    return pairs


def _power_of_two_rates() -> dict[str, float]:
    """Per-letter rates 2^-i so distinct letter-sets yield distinct sums."""
    return {chr(ord("a") + i): 2.0 ** -(i + 1) for i in range(26)}


def _count_tbody_rows(html: str) -> int:
    # <thead> has one <tr>; count total and subtract.
    total_tr = html.count("<tr")
    head_tr = html.count("<thead>")
    return total_tr - head_tr


# ---- Letter ranking -----------------------------------------------------------


def test_letter_ranking_caps_at_top_n_buckets() -> None:
    """With rates that force distinct scores per distinct letter-set, the renderer
    produces one row per unique score up to top_n. 60 generated words with
    power-of-two letter rates always produce more than 50 distinct letter-sets,
    so exactly 50 rows appear."""
    rates = _power_of_two_rates()
    html = render_letter_ranking(_ten_letter_words(), rates, top_n=50)
    assert _count_tbody_rows(html) == 50


def test_letter_ranking_collapses_exact_ties_into_fewer_rows() -> None:
    """Uniform rates make every distinct-letter-count tier score-identical; the
    renderer collapses those into buckets, so far fewer than top_n rows appear."""
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    html = render_letter_ranking(_ten_letter_words(), rates, top_n=50)
    assert _count_tbody_rows(html) < 50


def test_letter_ranking_transparency_lists_distinct_letters_sorted_by_rate() -> None:
    rates = {ch: 0.001 for ch in string.ascii_lowercase}
    rates.update({"a": 0.5, "b": 0.3, "c": 0.1, "d": 0.05, "e": 0.02})
    html = render_letter_ranking(["aabbccddee"], rates, top_n=1)
    assert "a b c d e" in html


def test_letter_ranking_is_sortable() -> None:
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    html = render_letter_ranking(["abcdefghij"], rates, top_n=1)
    assert 'class="freq-table sortable-table ranking-table"' in html
    assert 'class="sortable"' in html


def test_letter_ranking_exemplar_cascade_prefers_dict_resident() -> None:
    """Tied words with dict-resident member → exemplar is the dict word."""
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    # Three anagrams — same distinct-letter set, same score.
    words = ["bacdefghij", "abcdefghij", "cabdefghij"]
    us_dict = frozenset({"bacdefghij"})
    html = render_letter_ranking(words, rates, top_n=1, us_dict=us_dict)
    # Exemplar is the one in the dict, not alphabetically-first.
    assert '>bacdefghij' in html
    # Tied-badge indicates 2 other words in the bucket.
    assert "+2 more" in html


def test_letter_ranking_emits_expansion_shell_and_inline_bucket_data() -> None:
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    words = ["abcdefghij", "bacdefghij"]  # anagrams → one bucket
    html = render_letter_ranking(words, rates, top_n=1)
    assert 'id="expand-rank-letter"' in html
    assert 'class="bucket-expansion"' in html
    # Tied-word payload lives on the row as a data-attribute, not in a <script> island
    # (Zensical's instant-router choked on inline JSON script tags).
    assert "data-bucket-words=" in html
    assert "<script" not in html


def test_letter_ranking_singleton_bucket_has_no_click_markup() -> None:
    rates = {chr(ord("a") + i): 2.0 ** -(i + 1) for i in range(26)}
    html = render_letter_ranking(["abcdefghij"], rates, top_n=1)
    # Singleton bucket: no 'clickable' class, no 'more' badge.
    assert "clickable" not in html
    assert "more" not in html


# ---- Bigram ranking -----------------------------------------------------------


def test_bigram_ranking_caps_at_top_n_buckets() -> None:
    # Bigram-set collisions across generated words are common, so the bucket
    # count is input-dependent. The contract being tested is "never exceed top_n".
    rates = {
        f"{chr(ord('a') + i)}{chr(ord('a') + j)}": 2.0 ** -(i * 26 + j + 1)
        for i in range(26) for j in range(26)
    }
    html = render_bigram_ranking(_ten_letter_words(), rates, top_n=50)
    assert 1 <= _count_tbody_rows(html) <= 50


def test_bigram_ranking_transparency_top_3_by_rate_under_distinct_cap() -> None:
    """Under distinct-cap bigram scoring each bigram contributes its rate once,
    so transparency is top-3 distinct bigrams by rate (contribution = rate).
    'ababababcd' has distinct bigrams {ab, ba, bc, cd}."""
    rates = {"ab": 0.1, "ba": 0.0, "bc": 0.0, "cd": 0.25}
    html = render_bigram_ranking(["ababababcd"], rates, top_n=1)
    # Top 3 by rate: cd (0.25), ab (0.1), then ba and bc tie at 0.0 — alphabetical
    # tiebreak picks ba before bc.
    assert "cd, ab, ba" in html


def test_bigram_ranking_collapses_exact_ties() -> None:
    rates = {f"{a}{b}": 0.01 for a in "ab" for b in "ab"}
    # Two words with identical distinct-bigram sets score equal; collapse to 1 bucket.
    words = ["ababababab", "babababab" + "a"]  # both are ab/ba alternations
    html = render_bigram_ranking(words, rates, top_n=50)
    assert _count_tbody_rows(html) == 1


# ---- Trigram ranking ----------------------------------------------------------


def test_trigram_ranking_caps_at_top_n_buckets() -> None:
    start_rates = {
        f"{chr(ord('a') + i)}{chr(ord('a') + j)}{chr(ord('a') + k)}":
            2.0 ** -(i * 676 + j * 26 + k + 1)
        for i in range(5) for j in range(5) for k in range(5)
    }
    end_rates = dict(start_rates)
    html = render_trigram_ranking(_ten_letter_words(), start_rates, end_rates, top_n=50)
    assert _count_tbody_rows(html) <= 50


def test_trigram_ranking_shows_separate_start_end_columns() -> None:
    html = render_trigram_ranking(["abcdefghij"], {"abc": 0.1}, {"hij": 0.1}, top_n=1)
    assert "Start" in html
    assert "End" in html
    assert "abc" in html
    assert "hij" in html


def test_trigram_ranking_collapses_pre_ing_style_tier() -> None:
    """Words sharing start+end trigram score identically under trigram_score,
    so they collapse to one bucket even with many different middles."""
    start = {"pre": 0.01}
    end = {"ing": 0.04}
    words = ["preallying", "preambling", "prebidding", "prebinding"]
    html = render_trigram_ranking(words, start, end, top_n=50)
    assert _count_tbody_rows(html) == 1
    assert "+3 more" in html


# ---- Positional ranking -------------------------------------------------------


def test_positional_ranking_caps_at_top_n_buckets() -> None:
    letter_rates = _power_of_two_rates()
    first_rates = {ch: 2.0 ** -(i + 27) for i, ch in enumerate(string.ascii_lowercase)}
    last_rates = {ch: 2.0 ** -(i + 53) for i, ch in enumerate(string.ascii_lowercase)}
    html = render_positional_ranking(
        _ten_letter_words(), letter_rates, first_rates, last_rates, top_n=50
    )
    assert _count_tbody_rows(html) == 50


def test_positional_ranking_shows_separate_first_last_columns() -> None:
    letter_rates = {ch: 0.1 for ch in string.ascii_lowercase}
    html = render_positional_ranking(
        ["abcdefghij"], letter_rates, {"a": 0.1}, {"j": 0.2}, top_n=1
    )
    assert "First" in html
    assert "Last" in html


def test_positional_ranking_doubled_endpoint_word() -> None:
    letter_rates = {"a": 1.0}
    first_rates = {"a": 0.5}
    last_rates = {"a": 0.3}
    html = render_positional_ranking(
        ["aaaaaaaaaa"], letter_rates, first_rates, last_rates, top_n=1
    )
    assert "1.8000" in html


# ---- Shared structural assertions ---------------------------------------------


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


def test_all_ranking_tables_emit_expansion_shell() -> None:
    rates = {ch: 0.1 for ch in string.ascii_lowercase}
    bigram_rates = {f"{a}{b}": 0.01 for a in "abcd" for b in "abcd"}
    words = ["abcdefghij"]
    htmls = [
        (render_letter_ranking(words, rates, top_n=1), "rank-letter"),
        (render_bigram_ranking(words, bigram_rates, top_n=1), "rank-bigram"),
        (render_trigram_ranking(words, {"abc": 0.1}, {"hij": 0.1}, top_n=1), "rank-trigram"),
        (render_positional_ranking(words, rates, {"a": 0.1}, {"j": 0.1}, top_n=1), "rank-positional"),
    ]
    for html, table_id in htmls:
        assert f'id="expand-{table_id}"' in html
