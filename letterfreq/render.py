"""HTML renderers for the ten-letter page reference and ranking tables.

Each renderer takes count and rate dicts and returns an HTML string ready to
embed in a Markdown document. Tables use the existing `sortable-table` and
`freq-table` CSS classes; client-side sorting is provided by
`docs/js/sort-tables.js`.
"""

from __future__ import annotations

import string
from html import escape


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
            f'<td class="freq-letter">{letter}</td>'
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
