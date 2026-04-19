"""Tests for letterfreq.render reference-table functions.

These tests verify HTML structure (row counts, presence of sortable class,
column headers) — not visual appearance, which is verified in Phase 6's
end-to-end build.
"""

from __future__ import annotations

import string

from letterfreq.render import (
    render_bigram_table,
    render_first_last_pair,
    render_letter_table,
    render_trigram_pair,
)


# ---- Letter table -------------------------------------------------------------

# AC5.1
def test_letter_table_has_26_rows() -> None:
    counts = {ch: 100 + i for i, ch in enumerate(string.ascii_lowercase)}
    rates = {ch: count / 26000 for ch, count in counts.items()}
    html = render_letter_table(rates, counts, word_count=1000)
    # Each <tr> in tbody is one row; we have 1 thead row + 26 tbody rows = 27 total
    assert html.count("<tr>") == 27


def test_letter_table_is_sortable() -> None:
    counts = {ch: 100 for ch in string.ascii_lowercase}
    rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    html = render_letter_table(rates, counts, word_count=100)
    assert 'class="freq-table sortable-table"' in html
    assert 'class="sortable"' in html


# ---- Bigram table -------------------------------------------------------------

# AC5.2
def test_bigram_table_has_top_100_rows_when_more_available() -> None:
    # Generate 121 bigrams (11 × 11) so top_n=100 actually truncates
    pairs = [(a, b) for a in "abcdefghijk" for b in "abcdefghijk"]
    assert len(pairs) == 121
    counts = {f"{a}{b}": (i + 1) for i, (a, b) in enumerate(pairs)}
    rates = {k: v / sum(counts.values()) for k, v in counts.items()}
    html = render_bigram_table(rates, counts, word_count=500, top_n=100)
    assert html.count("<tr>") == 101  # 1 thead + 100 tbody (truncated from 121)


def test_bigram_table_truncates_to_top_n() -> None:
    counts = {f"a{ch}": i + 1 for i, ch in enumerate(string.ascii_lowercase)}  # 26 bigrams
    rates = {k: v / sum(counts.values()) for k, v in counts.items()}
    html = render_bigram_table(rates, counts, word_count=100, top_n=10)
    assert html.count("<tr>") == 11  # 1 thead + 10 tbody


def test_bigram_table_returns_all_when_fewer_than_top_n() -> None:
    counts = {"ab": 5, "cd": 3}
    rates = {"ab": 0.5, "cd": 0.3}
    html = render_bigram_table(rates, counts, word_count=10, top_n=100)
    assert html.count("<tr>") == 3  # 1 thead + 2 tbody


# ---- Trigram pair -------------------------------------------------------------

# AC5.3
def test_trigram_pair_has_50_rows_each_side() -> None:
    start_counts = {f"{a}{b}{c}": (i + 1)
                    for i, (a, b, c) in enumerate(
                        (a, b, c) for a in "abcdef" for b in "abcdef" for c in "abcdef"
                    )}  # 216 distinct trigrams
    end_counts = dict(start_counts)
    start_rates = {k: v / sum(start_counts.values()) for k, v in start_counts.items()}
    end_rates = dict(start_rates)
    html = render_trigram_pair(
        start_rates, start_counts, end_rates, end_counts, word_count=1000, top_n=50
    )
    # Each side: 1 thead + 50 tbody = 51 rows × 2 sides = 102 total
    assert html.count("<tr>") == 102


def test_trigram_pair_uses_ref_pair_class() -> None:
    html = render_trigram_pair({}, {"abc": 1}, {}, {"xyz": 1}, word_count=1, top_n=50)
    assert 'class="ref-pair"' in html


def test_trigram_pair_renders_both_sides() -> None:
    html = render_trigram_pair({}, {"abc": 1}, {}, {"xyz": 1}, word_count=1, top_n=50)
    assert "Most common start trigrams" in html
    assert "Most common end trigrams" in html


# ---- First/last pair ----------------------------------------------------------

# AC5.5
def test_first_last_pair_has_26_rows_each_side() -> None:
    first_counts = {ch: 100 for ch in string.ascii_lowercase}
    last_counts = {ch: 50 for ch in string.ascii_lowercase}
    first_rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    last_rates = {ch: 1 / 26 for ch in string.ascii_lowercase}
    html = render_first_last_pair(
        first_rates, first_counts, last_rates, last_counts, word_count=1000
    )
    # Each side: 1 thead + 26 tbody = 27 rows × 2 sides = 54 total
    assert html.count("<tr>") == 54


def test_first_last_pair_includes_letters_with_zero_count() -> None:
    """If a letter never appears as first/last, it should still get a row (count 0)."""
    first_counts = {"a": 100, "z": 1}  # missing b–y
    last_counts = {"e": 50}  # missing a–d, f–z
    first_rates = {"a": 0.99, "z": 0.01}
    last_rates = {"e": 1.0}
    html = render_first_last_pair(
        first_rates, first_counts, last_rates, last_counts, word_count=101
    )
    # Still 26+26 rows each side
    assert html.count("<tr>") == 54


def test_first_last_pair_uses_ref_pair_class() -> None:
    html = render_first_last_pair({}, {}, {}, {}, word_count=1)
    assert 'class="ref-pair"' in html
