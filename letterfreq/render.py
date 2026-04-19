"""HTML renderers for the ten-letter page reference and ranking tables.

Each renderer takes count and rate dicts and returns an HTML string ready to
embed in a Markdown document. Tables use the existing `sortable-table` and
`freq-table` CSS classes; client-side sorting is provided by
`docs/js/sort-tables.js`.
"""

from __future__ import annotations

import json
import string
from html import escape
from typing import Callable

from letterfreq.grouping import (
    GAP_EPSILON,
    exemplar,
    gap_cluster,
    sort_bucket_words,
)
from letterfreq.scoring import (
    bigram_score,
    letter_score,
    positional_endpoint_score,
    trigram_score,
)


def _bar_cell(rate: float, max_rate: float) -> str:
    """Render the visual bar cell as a CSS linear-gradient td."""
    pct = (rate / max_rate * 100) if max_rate > 0 else 0
    return (
        '<td class="freq-bar" style="background:linear-gradient(to right, '
        f"var(--md-primary-fg-color, #4051b5) {pct:.1f}%, transparent {pct:.1f}%)\"></td>"
    )


def render_letter_table(
    rates: dict[str, float],
    counts: dict[str, int],
    word_count: int,
) -> str:
    """Render the 26-row letter-frequency reference table for /ten/.

    Columns: Letter | Count | Per-word rate | Frequency bar.
    Sortable by Letter, Count, Per-word rate.
    """
    letters = sorted(string.ascii_lowercase)
    max_rate = max(rates.values(), default=0.0) or 1.0
    rows: list[str] = []
    for letter in letters:
        count = counts.get(letter, 0)
        rate = rates.get(letter, 0.0)
        per_word = count / word_count if word_count > 0 else 0.0
        rows.append(
            f"  <tr>"
            f'<td class="freq-letter">{escape(letter)}</td>'
            f'<td class="freq-count" data-value="{count}">{count:,}</td>'
            f'<td class="freq-rate" data-value="{per_word:.4f}">{per_word:.4f}</td>'
            f"{_bar_cell(rate, max_rate)}"
            f"</tr>"
        )
    return (
        '<table class="freq-table sortable-table">\n'
        "  <thead><tr>"
        '<th class="sortable" data-col="0">Letter</th>'
        '<th class="sortable" data-col="1">Count</th>'
        '<th class="sortable" data-col="2">Per word</th>'
        "<th>Frequency</th>"
        "</tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def render_bigram_table(
    rates: dict[str, float],
    counts: dict[str, int],
    word_count: int,
    top_n: int = 100,
) -> str:
    """Render the flat top-N bigram reference table for /ten/.

    Columns: Bigram | Count | Per-word rate | Frequency bar.
    Sortable. Sorted descending by count by default; tie-break alphabetical.
    """
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    if not items:
        return '<p><em>No bigrams.</em></p>'
    max_rate = max((rates.get(b, 0.0) for b, _ in items), default=0.0) or 1.0
    rows: list[str] = []
    for bigram, count in items:
        rate = rates.get(bigram, 0.0)
        per_word = count / word_count if word_count > 0 else 0.0
        rows.append(
            f"  <tr>"
            f'<td class="freq-letter">{escape(bigram)}</td>'
            f'<td class="freq-count" data-value="{count}">{count:,}</td>'
            f'<td class="freq-rate" data-value="{per_word:.4f}">{per_word:.4f}</td>'
            f"{_bar_cell(rate, max_rate)}"
            f"</tr>"
        )
    return (
        '<table class="freq-table sortable-table">\n'
        "  <thead><tr>"
        '<th class="sortable" data-col="0">Bigram</th>'
        '<th class="sortable" data-col="1">Count</th>'
        '<th class="sortable" data-col="2">Per word</th>'
        "<th>Frequency</th>"
        "</tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def _render_ranked_dict_table(
    counts: dict[str, int],
    rates: dict[str, float],
    word_count: int,
    label: str,
    top_n: int,
) -> str:
    """Internal helper: render a sortable top-N table from a {key: count} dict.

    Used by both trigram-pair and first/last-pair renderers. Each row:
    label-cell | count | per-word rate | bar.
    """
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    if not items:
        return f'<p><em>No {escape(label.lower())} entries.</em></p>'
    max_rate = max((rates.get(k, 0.0) for k, _ in items), default=0.0) or 1.0
    rows: list[str] = []
    for key, count in items:
        rate = rates.get(key, 0.0)
        per_word = count / word_count if word_count > 0 else 0.0
        rows.append(
            f"  <tr>"
            f'<td class="freq-letter">{escape(key)}</td>'
            f'<td class="freq-count" data-value="{count}">{count:,}</td>'
            f'<td class="freq-rate" data-value="{per_word:.4f}">{per_word:.4f}</td>'
            f"{_bar_cell(rate, max_rate)}"
            f"</tr>"
        )
    return (
        '<table class="freq-table sortable-table">\n'
        "  <thead><tr>"
        f'<th class="sortable" data-col="0">{escape(label)}</th>'
        '<th class="sortable" data-col="1">Count</th>'
        '<th class="sortable" data-col="2">Per word</th>'
        "<th>Frequency</th>"
        "</tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def render_trigram_pair(
    start_rates: dict[str, float],
    start_counts: dict[str, int],
    end_rates: dict[str, float],
    end_counts: dict[str, int],
    word_count: int,
    top_n: int = 50,
) -> str:
    """Render the side-by-side start/end trigram top-N tables for /ten/.

    Each side is a sortable top-N table (default top-50) with columns:
    Trigram | Count | Per-word rate | Frequency bar. The pair is wrapped in
    a `.ref-pair` grid container that stacks on narrow viewports.
    """
    start_table = _render_ranked_dict_table(
        start_counts, start_rates, word_count, "Start trigram", top_n
    )
    end_table = _render_ranked_dict_table(
        end_counts, end_rates, word_count, "End trigram", top_n
    )
    return (
        '<div class="ref-pair">\n'
        "<div>\n"
        "<h3>Most common start trigrams</h3>\n"
        f"{start_table}\n"
        "</div>\n"
        "<div>\n"
        "<h3>Most common end trigrams</h3>\n"
        f"{end_table}\n"
        "</div>\n"
        "</div>"
    )


def render_first_last_pair(
    first_rates: dict[str, float],
    first_counts: dict[str, int],
    last_rates: dict[str, float],
    last_counts: dict[str, int],
    word_count: int,
) -> str:
    """Render the side-by-side first-letter and last-letter 26-row tables.

    Same shape as render_trigram_pair, but each side is always 26 rows
    (one per a–z letter) and there is no top_n cap. Per DR8.
    """
    # Ensure all 26 letters appear even if absent from counts
    full_first = {ch: first_counts.get(ch, 0) for ch in string.ascii_lowercase}
    full_last = {ch: last_counts.get(ch, 0) for ch in string.ascii_lowercase}
    first_table = _render_ranked_dict_table(
        full_first, first_rates, word_count, "First letter", top_n=26
    )
    last_table = _render_ranked_dict_table(
        full_last, last_rates, word_count, "Last letter", top_n=26
    )
    return (
        '<div class="ref-pair">\n'
        "<div>\n"
        "<h3>Most common first letters</h3>\n"
        f"{first_table}\n"
        "</div>\n"
        "<div>\n"
        "<h3>Most common last letters</h3>\n"
        f"{last_table}\n"
        "</div>\n"
        "</div>"
    )


# --- Ranking-table renderers (Phase 5) ----------------------------------------


def _ranking_thead(columns: list[str]) -> str:
    """Render a sortable <thead> from a list of column headings."""
    cells = "".join(
        f'<th class="sortable" data-col="{i}">{escape(col)}</th>'
        for i, col in enumerate(columns)
    )
    return f"  <thead><tr>{cells}</tr></thead>\n"


def _score_all(
    words: list[str], score_fn: Callable[[str], float]
) -> list[tuple[str, float]]:
    """Score each word and return (word, score) pairs sorted desc by score, asc by word."""
    scored = [(w, score_fn(w)) for w in words]
    scored.sort(key=lambda sw: (-sw[1], sw[0]))
    return scored


def _tied_badge(bucket_size: int) -> str:
    """Small visual marker for the exemplar row when a bucket collapses multiple words."""
    if bucket_size <= 1:
        return ""
    return f' <span class="tied-count">+{bucket_size - 1} more</span>'


def _bucket_row_attrs(
    bucket_words: list[tuple[str, bool]],
) -> str:
    """Attributes for an exemplar <tr>. Only multi-word buckets become clickable.

    Single-word buckets get no clickable markup at all. Multi-word buckets carry
    their tied-word list as an HTML-escaped JSON payload in data-bucket-words,
    so JS reads the list directly off the row without a separate data island —
    an inline <script type="application/json"> tag broke Zensical's instant-router
    DOM processing (unexpected ':' during replaceWith).
    """
    if len(bucket_words) <= 1:
        return ""
    payload = json.dumps([[w, r] for w, r in bucket_words], ensure_ascii=True)
    return (
        ' class="bucket-row clickable" '
        f'data-bucket-words="{escape(payload, quote=True)}"'
    )


def _expansion_shell(table_id: str) -> str:
    """Empty expansion panel that JS populates on row click."""
    return (
        f'<div class="bucket-expansion" id="expand-{escape(table_id)}" '
        f'aria-live="polite"></div>'
    )


def render_letter_ranking(
    words_10: list[str],
    letter_rates: dict[str, float],
    top_n: int = 50,
    us_dict: frozenset[str] = frozenset(),
    eps: float = GAP_EPSILON,
) -> str:
    """Top-N buckets of ten-letter words by letter_score, with distinct-letter transparency.

    Scores are gap-clustered with threshold `eps` so near-ties collapse into one
    row. Each row shows an exemplar word (first dict-resident alphabetically,
    falling back to first alphabetically), the exemplar's distinct letters
    sorted by rate, and the bucket's top score. Buckets of size > 1 are
    clickable; tied words are rendered into the expansion panel by JS.
    """
    scored = _score_all(words_10, lambda w: letter_score(w, letter_rates))
    buckets = gap_cluster(scored, eps=eps)[:top_n]
    table_id = "rank-letter"
    rows: list[str] = []
    for rank, bucket in enumerate(buckets, start=1):
        bucket_words = [w for w, _ in bucket]
        ex = exemplar(bucket_words, us_dict)
        top_score = bucket[0][1]
        distinct_sorted = sorted(
            set(ex), key=lambda ch: (-letter_rates.get(ch, 0.0), ch)
        )
        letters_str = " ".join(distinct_sorted)
        sorted_pairs = sort_bucket_words(bucket_words, us_dict)
        rows.append(
            f"  <tr{_bucket_row_attrs(sorted_pairs)}>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(ex)}{_tied_badge(len(bucket_words))}</td>'
            f'<td class="freq-letters">{escape(letters_str)}</td>'
            f'<td class="freq-score" data-value="{top_score:.6f}">{top_score:.4f}</td>'
            f"</tr>"
        )
    return (
        f'<table class="freq-table sortable-table ranking-table" id="{table_id}">\n'
        + _ranking_thead(["Rank", "Word", "Distinct letters", "Score (letter)"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>\n"
        + _expansion_shell(table_id)
    )


def render_bigram_ranking(
    words_10: list[str],
    bigram_rates: dict[str, float],
    top_n: int = 50,
    us_dict: frozenset[str] = frozenset(),
    eps: float = GAP_EPSILON,
) -> str:
    """Top-N buckets of ten-letter words by bigram_score, with top-3 contributor transparency.

    Under distinct-cap bigram scoring, each bigram in a word contributes its
    rate exactly once regardless of how many times it appears. The contributor
    cell therefore lists the exemplar's top 3 distinct bigrams by raw rate
    (which equals contribution-to-score under the distinct cap).
    """
    scored = _score_all(words_10, lambda w: bigram_score(w, bigram_rates))
    buckets = gap_cluster(scored, eps=eps)[:top_n]
    table_id = "rank-bigram"
    rows: list[str] = []
    for rank, bucket in enumerate(buckets, start=1):
        bucket_words = [w for w, _ in bucket]
        ex = exemplar(bucket_words, us_dict)
        top_score = bucket[0][1]
        distinct_bigrams = {ex[i : i + 2] for i in range(len(ex) - 1)}
        contribs = sorted(
            distinct_bigrams,
            key=lambda bg: (-bigram_rates.get(bg, 0.0), bg),
        )[:3]
        contrib_str = ", ".join(contribs)
        sorted_pairs = sort_bucket_words(bucket_words, us_dict)
        rows.append(
            f"  <tr{_bucket_row_attrs(sorted_pairs)}>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(ex)}{_tied_badge(len(bucket_words))}</td>'
            f'<td class="freq-letters">{escape(contrib_str)}</td>'
            f'<td class="freq-score" data-value="{top_score:.6f}">{top_score:.4f}</td>'
            f"</tr>"
        )
    return (
        f'<table class="freq-table sortable-table ranking-table" id="{table_id}">\n'
        + _ranking_thead(["Rank", "Word", "Top contributors", "Score (bigram)"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>\n"
        + _expansion_shell(table_id)
    )


def render_trigram_ranking(
    words_10: list[str],
    start_rates: dict[str, float],
    end_rates: dict[str, float],
    top_n: int = 50,
    us_dict: frozenset[str] = frozenset(),
    eps: float = GAP_EPSILON,
) -> str:
    """Top-N buckets of ten-letter words by trigram_score (start + end).

    Columns: Rank | Word | Start | End | Score. Collapses the `pre___ing` tier
    and other start+end-trigram twins into a single row per distinct score.
    """
    scored = _score_all(
        words_10, lambda w: trigram_score(w, start_rates, end_rates)
    )
    buckets = gap_cluster(scored, eps=eps)[:top_n]
    table_id = "rank-trigram"
    rows: list[str] = []
    for rank, bucket in enumerate(buckets, start=1):
        bucket_words = [w for w, _ in bucket]
        ex = exemplar(bucket_words, us_dict)
        top_score = bucket[0][1]
        sorted_pairs = sort_bucket_words(bucket_words, us_dict)
        rows.append(
            f"  <tr{_bucket_row_attrs(sorted_pairs)}>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(ex)}{_tied_badge(len(bucket_words))}</td>'
            f'<td class="freq-letters">{escape(ex[:3])}</td>'
            f'<td class="freq-letters">{escape(ex[-3:])}</td>'
            f'<td class="freq-score" data-value="{top_score:.6f}">{top_score:.4f}</td>'
            f"</tr>"
        )
    return (
        f'<table class="freq-table sortable-table ranking-table" id="{table_id}">\n'
        + _ranking_thead(["Rank", "Word", "Start", "End", "Score (trigram)"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>\n"
        + _expansion_shell(table_id)
    )


def render_positional_ranking(
    words_10: list[str],
    letter_rates: dict[str, float],
    first_rates: dict[str, float],
    last_rates: dict[str, float],
    top_n: int = 50,
    us_dict: frozenset[str] = frozenset(),
    eps: float = GAP_EPSILON,
) -> str:
    """Top-N buckets of ten-letter words by positional_endpoint_score.

    Score = letter_score(w) + first_rate[w[0]] + last_rate[w[-1]]. Columns:
    Rank | Word | First | Last | Score. Both positional terms count even when
    first == last (no endpoint distinct cap).
    """
    scored = _score_all(
        words_10,
        lambda w: positional_endpoint_score(w, letter_rates, first_rates, last_rates),
    )
    buckets = gap_cluster(scored, eps=eps)[:top_n]
    table_id = "rank-positional"
    rows: list[str] = []
    for rank, bucket in enumerate(buckets, start=1):
        bucket_words = [w for w, _ in bucket]
        ex = exemplar(bucket_words, us_dict)
        top_score = bucket[0][1]
        sorted_pairs = sort_bucket_words(bucket_words, us_dict)
        rows.append(
            f"  <tr{_bucket_row_attrs(sorted_pairs)}>"
            f'<td class="freq-rank" data-value="{rank}">{rank}</td>'
            f'<td class="freq-word">{escape(ex)}{_tied_badge(len(bucket_words))}</td>'
            f'<td class="freq-letters">{escape(ex[0])}</td>'
            f'<td class="freq-letters">{escape(ex[-1])}</td>'
            f'<td class="freq-score" data-value="{top_score:.6f}">{top_score:.4f}</td>'
            f"</tr>"
        )
    return (
        f'<table class="freq-table sortable-table ranking-table" id="{table_id}">\n'
        + _ranking_thead(["Rank", "Word", "First", "Last", "Score (endpoint)"])
        + "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>\n"
        + _expansion_shell(table_id)
    )
