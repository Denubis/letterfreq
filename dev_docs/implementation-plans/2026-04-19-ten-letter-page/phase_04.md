# Ten-Letter Page Implementation Plan — Phase 4: Reference-table rendering

**Goal:** Implement the four reference-table HTML renderers in a new `letterfreq/render.py` module: a 26-row letter-frequency table, a flat top-100 bigram table, a side-by-side start/end trigram pair, and a side-by-side first-letter/last-letter pair. Append a small CSS rule for the side-by-side `.ref-pair` layout to `docs/css/heatmap.css`.

**Architecture:** Pure Python string-builders. Each function takes baseline counts/rates and returns an HTML string. Reuses the existing `sortable-table` and `freq-table` CSS classes (verified present in `heatmap.css` from Phase 1's investigation). No new JS — sorting comes from existing `sort-tables.js`.

**Tech Stack:** Python 3.14+, pytest. CSS: standard grid layout. No new dependencies.

**Scope:** Phase 4 of 7 from `/home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md`.

**Codebase verified:** 2026-04-19. `docs/css/heatmap.css` is 214 lines; defines `.freq-table`, `.freq-bar`, `.heatmap`, `.sortable`. ABSENT: `.ref-pair`, `.trigram-pair`. `letterfreq/__init__.py` and `letterfreq/reference.py` exist after Phase 2; `letterfreq/scoring.py` after Phase 3.

**Phase Type:** functionality

---

## Acceptance Criteria Coverage

This phase implements and tests:

### ten-letter-page.AC5: Reference tables render correctly on /ten/
- **ten-letter-page.AC5.1 Success:** Letter-frequency table has 26 rows.
- **ten-letter-page.AC5.2 Success:** Bigram top-100 table has exactly 100 rows.
- **ten-letter-page.AC5.3 Success:** Start- and end-trigram tables have 50 rows each, side-by-side in wide viewport, stacked in narrow viewport.
- **ten-letter-page.AC5.4 Success:** All four reference table sections expose sortable column headers (`<th class="sortable">`) and respond to click-to-sort.
- **ten-letter-page.AC5.5 Success:** First-letter and last-letter frequency tables each have 26 rows, side-by-side in wide viewport, stacked in narrow viewport (same layout pattern as the start/end trigram pair).

(AC5.4 click-to-sort behaviour relies on existing `sort-tables.js`; visual verification deferred to Phase 6 end-to-end build.)

---

## Implementation Tasks

<!-- START_TASK_1 -->
### Task 1: Append `.ref-pair` CSS to `docs/css/heatmap.css`

**Files:**
- Modify: `/home/brian/llm/letterfreq/docs/css/heatmap.css` (append at end)

**Implementation:**

Append the following block at the end of `docs/css/heatmap.css`:

```css

/* --- Side-by-side reference-table pair (used by start/end trigrams and first/last letters on /ten/) --- */
.ref-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin: 1rem 0;
}

.ref-pair > * {
  min-width: 0; /* allow children to shrink within their grid cell */
}

@media (max-width: 768px) {
  .ref-pair {
    grid-template-columns: 1fr;
  }
}
```

**Verification:**

```bash
grep -n "ref-pair" docs/css/heatmap.css
```

Expected: shows the new rules (3 occurrences of the `ref-pair` selector token in the appended block).

```bash
uv run zensical build --clean
```

Expected: build succeeds. CSS file copied to `site/css/heatmap.css`. (Visual verification deferred to Phase 6.)

**Commit (combined with Task 2):**
<!-- END_TASK_1 -->

<!-- START_SUBCOMPONENT_A (tasks 2-3) -->
<!-- START_TASK_2 -->
### Task 2: Implement `letterfreq/render.py` reference-table renderers

**Verifies (when paired with Task 3 tests):** ten-letter-page.AC5.1, AC5.2, AC5.3, AC5.5 (structural shape; sortability via class attributes).

**Files:**
- Create: `/home/brian/llm/letterfreq/letterfreq/render.py`

**Implementation:**

```python
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
```

**Implementation notes:**
- All single-character keys (letters) and short trigrams are passed through `html.escape()` defensively even though baseline data is pre-filtered to a–z; this mirrors the safety practice in existing `main.py` rendering.
- `_render_ranked_dict_table` is the shared helper for trigram-pair and first/last-pair. It sorts descending by count with alphabetical tie-break, mirroring `top_n_by_score` semantics for consistency.
- `render_first_last_pair` always shows all 26 letters (per AC5.5: "26 rows each") rather than truncating; the existing `freq-table` CSS handles the visual.
- No `data-value` on the bigram/trigram label column because alphabetical sort works directly on text content.

**No commit yet** — wait for Task 3 to write tests.
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Tests for reference-table renderers

**Verifies:** ten-letter-page.AC5.1, AC5.2, AC5.3, AC5.5 (row counts; structural HTML).

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_render_reference.py`

**Implementation:**

```python
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
```

**Verification:**

```bash
uv run pytest tests/test_render_reference.py -v
```

Expected: 11 tests pass.

Run full suite:

```bash
uv run pytest -q
```

Expected: all tests pass (test_frequencies, test_reference, test_scoring, test_render_reference).

**Commit (combined with Tasks 1 + 2):**

```bash
git add docs/css/heatmap.css letterfreq/render.py tests/test_render_reference.py
git commit -m "feat: letterfreq.render — reference-table renderers + .ref-pair CSS"
```
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->
