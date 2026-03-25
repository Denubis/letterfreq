"""Compute overall letter frequencies from five-letter English words and generate docs/index.md."""

from __future__ import annotations

import json
import re
import string
from pathlib import Path

import polars as pl

WORD_FILE = Path("/usr/share/dict/words")
DOCS_DIR = Path(__file__).parent / "docs"
DATA_DIR = DOCS_DIR / "data"
INDEX_MD = DOCS_DIR / "index.md"


def load_words(path: Path = WORD_FILE) -> list[str]:
    """Read word list and return only lowercase five-letter words."""
    pattern = re.compile(r"^[a-z]{5}$")
    text = path.read_text()
    return [w for w in text.splitlines() if pattern.match(w)]


def compute_overall_frequencies(words: list[str]) -> pl.DataFrame:
    """Compute overall letter frequency counts.

    Returns a DataFrame with columns: letter, len (count), sorted by count descending.
    """
    freq = (
        pl.DataFrame({"word": words})
        .select(pl.col("word").str.split("").explode().drop_nulls().alias("letter"))
        .group_by("letter")
        .len()
        .sort("len", descending=True)
    )
    return freq


def compute_positional_unigrams(words: list[str]) -> dict[str, list[int]]:
    """Compute letter frequency at each position (1-5).

    Returns a dict mapping each letter to a list of 5 counts:
    {letter: [pos1_count, pos2_count, pos3_count, pos4_count, pos5_count]}
    """
    df = pl.DataFrame({"word": words})

    # Extract each position as a separate column
    df = df.with_columns(
        pl.col("word").str.slice(i, 1).alias(f"pos{i + 1}") for i in range(5)
    )

    # Unpivot from wide to long format
    long = df.drop("word").unpivot(variable_name="position", value_name="letter")

    # Group by letter and position, count occurrences
    counts = long.group_by(["letter", "position"]).len()

    # Pivot to get letter × position matrix
    matrix = counts.pivot(on="position", index="letter", values="len").sort("letter")

    # Fill nulls with 0 and build result dict
    result: dict[str, list[int]] = {}
    for row in matrix.iter_rows(named=True):
        letter = row["letter"]
        result[letter] = [row.get(f"pos{i + 1}", 0) or 0 for i in range(5)]

    # Ensure all 26 letters are present (rare letters may not appear at all positions)
    for letter in string.ascii_lowercase:
        result.setdefault(letter, [0, 0, 0, 0, 0])

    return result


def compute_bigrams(words: list[str]) -> dict[str, dict[str, dict[str, int]]]:
    """Compute bigram frequencies for adjacent position pairs.

    Returns a dict keyed by pair name (e.g. "1_2", "2_3", "3_4", "4_5")
    with values being nested dicts: {first_letter: {second_letter: count}}.
    Sparse representation — zero-count pairs omitted.
    """
    df = pl.DataFrame({"word": words})
    result: dict[str, dict[str, dict[str, int]]] = {}

    for i in range(4):
        pair_name = f"{i + 1}_{i + 2}"
        counts = (
            df.select(
                pl.col("word").str.slice(i, 1).alias("first"),
                pl.col("word").str.slice(i + 1, 1).alias("second"),
            )
            .group_by(["first", "second"])
            .len()
        )

        pair_dict: dict[str, dict[str, int]] = {}
        for row in counts.iter_rows(named=True):
            first = row["first"]
            second = row["second"]
            count = row["len"]
            pair_dict.setdefault(first, {})[second] = count

        result[pair_name] = pair_dict

    return result


def compute_trigrams(
    words: list[str],
) -> tuple[dict[str, dict[str, dict[str, dict[str, int]]]], dict[str, dict[str, dict[str, int]]]]:
    """Compute trigram gap frequencies for 3 gap positions x 3 word windows.

    Windows: positions 1-2-3, 2-3-4, 3-4-5 (1-indexed).
    Gap positions: 1st, 2nd, 3rd letter in trigram.

    known1 = lower-indexed word position, known2 = higher-indexed.

    Returns (detail, summary) where:
    - detail: {grid_name: {known1: {known2: {gap_letter: count}}}}
    - summary: {grid_name: {known1: {known2: total_count}}}
    """
    # Define the 9 grids: (grid_name, gap_word_pos, known1_word_pos, known2_word_pos)
    # All positions are 0-indexed into the word
    windows = [(0, 1, 2), (1, 2, 3), (2, 3, 4)]  # win123, win234, win345
    window_names = ["win123", "win234", "win345"]

    grids: list[tuple[str, int, int, int]] = []
    for win_name, (p1, p2, p3) in zip(window_names, windows, strict=True):
        # gap1: gap at p1, known at p2 (known1), p3 (known2)
        grids.append((f"gap1_{win_name}", p1, p2, p3))
        # gap2: gap at p2, known at p1 (known1), p3 (known2)
        grids.append((f"gap2_{win_name}", p2, p1, p3))
        # gap3: gap at p3, known at p1 (known1), p2 (known2)
        grids.append((f"gap3_{win_name}", p3, p1, p2))

    df = pl.DataFrame({"word": words})

    # Pre-extract all 5 positions
    df = df.with_columns(
        pl.col("word").str.slice(i, 1).alias(f"p{i}") for i in range(5)
    )

    detail: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
    summary: dict[str, dict[str, dict[str, int]]] = {}

    for grid_name, gap_pos, k1_pos, k2_pos in grids:
        counts = (
            df.select(
                pl.col(f"p{k1_pos}").alias("known1"),
                pl.col(f"p{k2_pos}").alias("known2"),
                pl.col(f"p{gap_pos}").alias("gap"),
            )
            .group_by(["known1", "known2", "gap"])
            .len()
        )

        grid_detail: dict[str, dict[str, dict[str, int]]] = {}
        grid_summary: dict[str, dict[str, int]] = {}

        for row in counts.iter_rows(named=True):
            k1 = row["known1"]
            k2 = row["known2"]
            gap = row["gap"]
            count = row["len"]
            grid_detail.setdefault(k1, {}).setdefault(k2, {})[gap] = count
            grid_summary.setdefault(k1, {})[k2] = (
                grid_summary.get(k1, {}).get(k2, 0) + count
            )

        detail[grid_name] = grid_detail
        summary[grid_name] = grid_summary

    return detail, summary


def get_neighbour_distributions(
    bigrams: dict[str, dict[str, dict[str, int]]], letter: str, position: int
) -> dict[str, dict[str, int]]:
    """Return neighbour frequency distributions for a letter at a given position.

    For position 1: only right neighbour (from "1_2" grid, row slice).
    For position 5: only left neighbour (from "4_5" grid, column slice).
    For positions 2-4: both left and right.

    Left neighbour: from the (position-1)_(position) grid, column slice —
        all first_letters paired with this letter as second_letter.
    Right neighbour: from the (position)_(position+1) grid, row slice —
        this letter's row.
    """
    result: dict[str, dict[str, int]] = {}

    # Left neighbour: letters at position-1 that precede this letter at position
    if position > 1:
        pair_key = f"{position - 1}_{position}"
        pair_data = bigrams[pair_key]
        left: dict[str, int] = {}
        for first_letter, seconds in pair_data.items():
            count = seconds.get(letter, 0)
            if count > 0:
                left[first_letter] = count
        result["left"] = left

    # Right neighbour: letters at position+1 that follow this letter at position
    if position < 5:
        pair_key = f"{position}_{position + 1}"
        pair_data = bigrams[pair_key]
        right = {sec: cnt for sec, cnt in pair_data.get(letter, {}).items() if cnt > 0}
        result["right"] = right

    return result


def generate_frequency_table_html(freq: pl.DataFrame, word_count: int) -> str:
    """Generate an HTML frequency table with bar visualisation."""
    max_count = freq["len"].max()
    rows: list[str] = []
    for row in freq.iter_rows(named=True):
        letter = row["letter"]
        count = row["len"]
        pct = count / max_count * 100
        freq_per_word = count / word_count
        rows.append(
            f'  <tr>'
            f'<td class="freq-letter">{letter}</td>'
            f'<td class="freq-count">{count:,}</td>'
            f'<td class="freq-rate">{freq_per_word:.3f}</td>'
            f'<td class="freq-bar" style="background:linear-gradient(to right, '
            f'var(--md-primary-fg-color, #4051b5) {pct:.1f}%, transparent {pct:.1f}%)">'
            f'</td>'
            f'</tr>'
        )
    return (
        '<table class="freq-table">\n'
        "  <thead><tr>"
        '<th>Letter</th><th>Count</th><th>Per word</th><th>Frequency</th>'
        "</tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def _heatmap_cell(count: int, max_count: int) -> str:
    """Render a single heatmap <td> using a CSS custom property for intensity."""
    intensity = count / max_count if max_count else 0
    return f'<td style="--heat: {intensity:.3f}">{count:,}</td>'


def generate_heatmap_html(unigrams: dict[str, list[int]]) -> str:
    """Generate an HTML heatmap table for positional unigram frequencies."""
    # Find max count across the entire grid for colour scaling
    max_count = max(c for counts in unigrams.values() for c in counts) or 1

    rows: list[str] = []
    for letter in sorted(unigrams):
        cells = [_heatmap_cell(count, max_count) for count in unigrams[letter]]
        rows.append(
            f'  <tr><td class="row-label">{letter}</td>{"".join(cells)}</tr>'
        )

    header = (
        "  <thead><tr><th></th>"
        + "".join(f"<th>Pos {i}</th>" for i in range(1, 6))
        + "</tr></thead>"
    )
    return (
        '<table class="heatmap">\n'
        f"{header}\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def _neighbour_bars_html(
    bigrams: dict[str, dict[str, dict[str, int]]], letter: str, pos: int
) -> str:
    """Generate the neighbour frequency bars HTML for a letter at a position."""
    neighbours = get_neighbour_distributions(bigrams, letter, pos)
    parts: list[str] = []

    if "left" in neighbours and neighbours["left"]:
        sorted_left = sorted(neighbours["left"].items(), key=lambda x: x[1], reverse=True)
        max_left = sorted_left[0][1] if sorted_left else 1
        parts.append(f"<h4>Position {pos - 1} \u2192 {letter}</h4>")
        for nb_letter, count in sorted_left:
            width = count / max_left * 100
            parts.append(
                f'<div class="bar-row">'
                f'<span class="bar-label">{nb_letter}</span>'
                f'<span class="bar" style="width: {width:.1f}%"></span>'
                f'<span class="bar-count">{count}</span>'
                f"</div>"
            )

    if "right" in neighbours and neighbours["right"]:
        sorted_right = sorted(neighbours["right"].items(), key=lambda x: x[1], reverse=True)
        max_right = sorted_right[0][1] if sorted_right else 1
        parts.append(f"<h4>{letter} \u2192 Position {pos + 1}</h4>")
        for nb_letter, count in sorted_right:
            width = count / max_right * 100
            parts.append(
                f'<div class="bar-row">'
                f'<span class="bar-label">{nb_letter}</span>'
                f'<span class="bar" style="width: {width:.1f}%"></span>'
                f'<span class="bar-count">{count}</span>'
                f"</div>"
            )

    return "\n".join(parts)


def generate_bigram_html(bigrams: dict[str, dict[str, dict[str, int]]]) -> str:
    """Generate collapsible bigram heatmap grids for all 4 adjacent position pairs."""
    letters = list(string.ascii_lowercase)
    sections: list[str] = []

    for i in range(4):
        pair_name = f"{i + 1}_{i + 2}"
        pair_data = bigrams[pair_name]
        pos_a = i + 1  # the row-header position

        # Find max count for this grid's normalisation
        max_count = max(
            (count for second_dict in pair_data.values() for count in second_dict.values()),
            default=1,
        )

        rows: list[str] = []
        for first in letters:
            cells: list[str] = []
            for second in letters:
                count = pair_data.get(first, {}).get(second, 0)
                cells.append(_heatmap_cell(count, max_count))

            # Check if this letter has any occurrences at this position
            row_sum = sum(pair_data.get(first, {}).values())
            if row_sum == 0:
                # Plain text — no drill-down for zero-occurrence letters
                header_cell = f'<th class="row-label">{first}</th>'
            else:
                bars_html = _neighbour_bars_html(bigrams, first, pos_a)
                header_cell = (
                    "<th>"
                    '<details class="drill-down">'
                    f"<summary>{first}</summary>"
                    f'<div class="neighbour-bars">{bars_html}</div>'
                    "</details>"
                    "</th>"
                )

            rows.append(f"  <tr>{header_cell}{''.join(cells)}</tr>")

        header_cells = "".join(f"<th>{ch}</th>" for ch in letters)
        header = f"  <thead><tr><th></th>{header_cells}</tr></thead>"

        table = (
            '<table class="heatmap bigram-grid">\n'
            f"{header}\n"
            "  <tbody>\n"
            + "\n".join(rows)
            + "\n  </tbody>\n</table>"
        )

        sections.append(
            f"<details>\n"
            f"<summary>Positions {i + 1}\u2013{i + 2}</summary>\n"
            f"{table}\n"
            f"</details>"
        )

    return "\n\n".join(sections)


def _trigram_cell(count: int, max_count: int, known1: str, known2: str) -> str:
    """Render a single trigram heatmap <td> with data attributes for JS interaction."""
    if count == 0:
        return '<td class="trigram-cell empty"></td>'
    intensity = count / max_count if max_count else 0
    return (
        f'<td class="trigram-cell" data-known1="{known1}" data-known2="{known2}"'
        f' data-count="{count}" style="--heat: {intensity:.3f}">{count:,}</td>'
    )


def generate_trigram_html(
    trigram_summary: dict[str, dict[str, dict[str, int]]],
) -> str:
    """Generate 9 heatmap grids under Positional Trigrams, organised by gap position then window."""
    letters = list(string.ascii_lowercase)
    sections: list[str] = []

    gap_labels = {
        1: "Gap at position 1 (_XY)",
        2: "Gap at position 2 (X_Y)",
        3: "Gap at position 3 (XY_)",
    }
    window_labels = {
        "win123": "Word positions 1-2-3",
        "win234": "Word positions 2-3-4",
        "win345": "Word positions 3-4-5",
    }

    for gap_pos in (1, 2, 3):
        gap_section_parts: list[str] = [f"### {gap_labels[gap_pos]}\n"]

        for win_name, win_label in window_labels.items():
            grid_name = f"gap{gap_pos}_{win_name}"
            grid_data = trigram_summary.get(grid_name, {})

            # Find max count for normalisation
            max_count = max(
                (count for k2_dict in grid_data.values() for count in k2_dict.values()),
                default=1,
            )

            rows: list[str] = []
            for k1 in letters:
                cells: list[str] = []
                for k2 in letters:
                    count = grid_data.get(k1, {}).get(k2, 0)
                    cells.append(_trigram_cell(count, max_count, k1, k2))
                rows.append(
                    f'  <tr><td class="row-label">{k1}</td>{"".join(cells)}</tr>'
                )

            header_cells = "".join(f"<th>{ch}</th>" for ch in letters)
            header = f"  <thead><tr><th></th>{header_cells}</tr></thead>"

            table = (
                f'<table class="heatmap trigram-grid" data-grid="{grid_name}">\n'
                f"{header}\n"
                "  <tbody>\n"
                + "\n".join(rows)
                + "\n  </tbody>\n</table>\n"
                f'<div class="trigram-expansion" id="expand-{grid_name}"></div>'
            )

            gap_section_parts.append(f"#### {win_label}\n\n{table}\n")

        sections.append("\n".join(gap_section_parts))

    return "\n".join(sections)


def generate_page(
    words: list[str],
    freq: pl.DataFrame,
    trigram_summary: dict[str, dict[str, dict[str, int]]] | None = None,
) -> str:
    """Generate the full docs/index.md content."""
    word_count = len(words)
    table_html = generate_frequency_table_html(freq, word_count)
    unigrams = compute_positional_unigrams(words)
    heatmap_html = generate_heatmap_html(unigrams)
    bigrams = compute_bigrams(words)
    bigram_html = generate_bigram_html(bigrams)

    trigram_section = ""
    if trigram_summary is not None:
        trigram_html = generate_trigram_html(trigram_summary)
        trigram_section = f"\n\n## Positional Trigrams\n\n{trigram_html}\n"

    return (
        "---\n"
        "icon: null\n"
        "---\n\n"
        "# Five-Letter Word Frequencies\n\n"
        f"Analysis of **{word_count:,}** five-letter words "
        f"from `/usr/share/dict/words`.\n\n"
        "## Overall Letter Frequencies\n\n"
        f"{table_html}\n\n"
        "## Positional Unigrams\n\n"
        f"{heatmap_html}\n\n"
        "## Positional Bigrams\n\n"
        f"{bigram_html}"
        f"{trigram_section}"
    )


def main() -> None:
    words = load_words()
    freq = compute_overall_frequencies(words)
    trigram_detail, trigram_summary = compute_trigrams(words)

    # Write trigram detail data as JSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    trigrams_json = DATA_DIR / "trigrams.json"
    trigrams_json.write_text(json.dumps(trigram_detail, sort_keys=True))

    page = generate_page(words, freq, trigram_summary)
    INDEX_MD.parent.mkdir(parents=True, exist_ok=True)
    INDEX_MD.write_text(page)
    print(f"Generated {INDEX_MD} ({len(words)} words, {freq['len'].sum()} total letters)")
    print(f"Generated {trigrams_json} ({len(trigram_detail)} grids)")


if __name__ == "__main__":
    main()
