"""Compute letter frequencies from five-letter English words and generate docs/index.md."""

from __future__ import annotations

import json
import string
from pathlib import Path

import polars as pl

WORD_FILE = Path(__file__).parent / "data" / "words.txt"
DOCS_DIR = Path(__file__).parent / "docs"
DATA_DIR = DOCS_DIR / "data"
INDEX_MD = DOCS_DIR / "index.md"


def load_words(path: Path = WORD_FILE) -> list[str]:
    """Read pre-filtered five-letter word list (one word per line, lowercase)."""
    return [w for w in path.read_text().splitlines() if w]


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
    df = df.with_columns(
        pl.col("word").str.slice(i, 1).alias(f"pos{i + 1}") for i in range(5)
    )
    long = df.drop("word").unpivot(variable_name="position", value_name="letter")
    counts = long.group_by(["letter", "position"]).len()
    matrix = counts.pivot(on="position", index="letter", values="len").sort("letter")

    result: dict[str, list[int]] = {}
    for row in matrix.iter_rows(named=True):
        letter = row["letter"]
        result[letter] = [row.get(f"pos{i + 1}", 0) or 0 for i in range(5)]

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

    Returns (detail, summary) where:
    - detail: {grid_name: {known1: {known2: {gap_letter: count}}}}
    - summary: {grid_name: {known1: {known2: total_count}}}
    """
    windows = [(0, 1, 2), (1, 2, 3), (2, 3, 4)]
    window_names = ["win123", "win234", "win345"]

    grids: list[tuple[str, int, int, int]] = []
    for win_name, (p1, p2, p3) in zip(window_names, windows, strict=True):
        grids.append((f"gap1_{win_name}", p1, p2, p3))
        grids.append((f"gap2_{win_name}", p2, p1, p3))
        grids.append((f"gap3_{win_name}", p3, p1, p2))

    df = pl.DataFrame({"word": words})
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
    """Return neighbour frequency distributions for a letter at a given position."""
    result: dict[str, dict[str, int]] = {}

    if position > 1:
        pair_key = f"{position - 1}_{position}"
        pair_data = bigrams[pair_key]
        left: dict[str, int] = {}
        for first_letter, seconds in pair_data.items():
            count = seconds.get(letter, 0)
            if count > 0:
                left[first_letter] = count
        result["left"] = left

    if position < 5:
        pair_key = f"{position}_{position + 1}"
        pair_data = bigrams[pair_key]
        right = {sec: cnt for sec, cnt in pair_data.get(letter, {}).items() if cnt > 0}
        result["right"] = right

    return result


# --- HTML generation ---


def _col_maxes(data: dict[str, list[int]], ncols: int) -> list[int]:
    """Compute per-column max values for independent colour normalisation."""
    return [max((data[k][c] for k in data), default=1) or 1 for c in range(ncols)]


def _grid_col_maxes(
    grid_data: dict[str, dict[str, int]], letters: list[str],
) -> dict[str, int]:
    """Compute per-column max for a 26×26 grid (keyed by column letter)."""
    result: dict[str, int] = {}
    for col in letters:
        col_max = max(
            (grid_data.get(row, {}).get(col, 0) for row in letters), default=1
        )
        result[col] = col_max or 1
    return result


def _heatmap_td(count: int, col_max: int) -> str:
    """Render a heatmap <td> with data-value and per-column normalised --heat."""
    intensity = count / col_max if col_max else 0
    if count == 0:
        return f'<td data-value="0" style="--heat: 0"></td>'
    return f'<td data-value="{count}" style="--heat: {intensity:.3f}">{count:,}</td>'


def generate_frequency_table_html(freq: pl.DataFrame, word_count: int) -> str:
    """Generate the overall frequency table with bar visualisation."""
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
            f'<td class="freq-count" data-value="{count}">{count:,}</td>'
            f'<td class="freq-rate" data-value="{freq_per_word:.4f}">{freq_per_word:.3f}</td>'
            f'<td class="freq-bar" style="background:linear-gradient(to right, '
            f'var(--md-primary-fg-color, #4051b5) {pct:.1f}%, transparent {pct:.1f}%)">'
            f'</td>'
            f'</tr>'
        )
    return (
        '<table class="freq-table sortable-table">\n'
        "  <thead><tr>"
        '<th class="sortable" data-col="0">Letter</th>'
        '<th class="sortable" data-col="1">Count</th>'
        '<th class="sortable" data-col="2">Per word</th>'
        '<th>Frequency</th>'
        "</tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def generate_heatmap_html(unigrams: dict[str, list[int]]) -> str:
    """Generate the positional unigram table with per-column normalisation and sorting."""
    col_max = _col_maxes(unigrams, 5)

    rows: list[str] = []
    for letter in sorted(unigrams):
        cells: list[str] = []
        for pos in range(5):
            count = unigrams[letter][pos]
            cells.append(_heatmap_td(count, col_max[pos]))
        rows.append(
            f'  <tr><td class="row-label">{letter}</td>{"".join(cells)}</tr>'
        )

    header = (
        '  <thead><tr><th class="sortable" data-col="0">Letter</th>'
        + "".join(
            f'<th class="sortable" data-col="{i}">Pos {i}</th>'
            for i in range(1, 6)
        )
        + "</tr></thead>"
    )
    return (
        '<table class="heatmap sortable-table">\n'
        f"{header}\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>"
    )


def generate_bigram_html(bigrams: dict[str, dict[str, dict[str, int]]]) -> str:
    """Generate collapsible bigram grids with plain row labels and per-column normalisation.

    Drill-down data is embedded as JSON in data attributes on the grid,
    rendered by JS on row click into an expansion panel below the grid.
    """
    letters = list(string.ascii_lowercase)
    sections: list[str] = []

    for i in range(4):
        pair_name = f"{i + 1}_{i + 2}"
        pair_data = bigrams[pair_name]
        pos_a = i + 1

        # Per-column normalisation
        col_max = _grid_col_maxes(pair_data, letters)

        pos_b = i + 2
        rows: list[str] = []
        for first in letters:
            cells: list[str] = []
            for second in letters:
                count = pair_data.get(first, {}).get(second, 0)
                intensity = count / col_max[second] if col_max[second] else 0
                if count == 0:
                    cells.append('<td class="bigram-cell" data-value="0" style="--heat: 0"></td>')
                else:
                    cells.append(
                        f'<td class="bigram-cell" data-value="{count}"'
                        f' data-row="{first}" data-col-letter="{second}"'
                        f' data-row-pos="{pos_a}" data-col-pos="{pos_b}"'
                        f' style="--heat: {intensity:.3f}">{count:,}</td>'
                    )
            rows.append(
                f'  <tr><td class="row-label bigram-row" '
                f'data-letter="{first}" data-pos="{pos_a}">'
                f'{first}</td>{"".join(cells)}</tr>'
            )

        header_cells = "".join(
            f'<th class="sortable bigram-col" data-col="{idx + 1}"'
            f' data-letter="{ch}" data-pos="{pos_b}">{ch}</th>'
            for idx, ch in enumerate(letters)
        )
        header = f'  <thead><tr><th class="sortable" data-col="0"></th>{header_cells}</tr></thead>'

        grid_id = f"bigram-{pair_name}"
        table = (
            f'<table class="heatmap bigram-grid sortable-table" id="{grid_id}"'
            f' data-pair="{pair_name}">\n'
            f"{header}\n"
            "  <tbody>\n"
            + "\n".join(rows)
            + "\n  </tbody>\n</table>\n"
            f'<div class="bigram-expansion" id="expand-{grid_id}"></div>'
        )

        sections.append(
            f"### Positions {i + 1}\u2013{i + 2}\n\n"
            f"{table}\n"
        )

    return "\n\n".join(sections)


def generate_trigram_html(
    trigram_summary: dict[str, dict[str, dict[str, int]]],
) -> str:
    """Generate 9 trigram heatmap grids with per-column normalisation."""
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

            col_max = _grid_col_maxes(grid_data, letters)

            rows: list[str] = []
            for k1 in letters:
                cells: list[str] = []
                for k2 in letters:
                    count = grid_data.get(k1, {}).get(k2, 0)
                    cm = col_max[k2]
                    if count == 0:
                        cells.append(
                            '<td class="trigram-cell empty" data-value="0"></td>'
                        )
                    else:
                        intensity = count / cm if cm else 0
                        cells.append(
                            f'<td class="trigram-cell" data-known1="{k1}" '
                            f'data-known2="{k2}" data-count="{count}" '
                            f'data-value="{count}" style="--heat: {intensity:.3f}">'
                            f"{count:,}</td>"
                        )
                rows.append(
                    f'  <tr><td class="row-label">{k1}</td>{"".join(cells)}</tr>'
                )

            header_cells = "".join(
                f'<th class="sortable" data-col="{idx + 1}">{ch}</th>'
                for idx, ch in enumerate(letters)
            )
            header = f'  <thead><tr><th class="sortable" data-col="0"></th>{header_cells}</tr></thead>'

            table = (
                f'<table class="heatmap trigram-grid sortable-table" data-grid="{grid_name}">\n'
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
        f"Analysis of **{word_count:,}** five-letter words from the "
        "[dwyl/english-words](https://github.com/dwyl/english-words) "
        "corpus (Unlicense).\n\n"
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

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    trigrams_json = DATA_DIR / "trigrams.json"
    trigrams_json.write_text(json.dumps(trigram_detail, sort_keys=True))

    # Write bigram data for JS drill-downs
    bigrams = compute_bigrams(words)
    bigrams_json = DATA_DIR / "bigrams.json"
    bigrams_json.write_text(json.dumps(bigrams, sort_keys=True))

    page = generate_page(words, freq, trigram_summary)
    INDEX_MD.parent.mkdir(parents=True, exist_ok=True)
    INDEX_MD.write_text(page)
    print(f"Generated {INDEX_MD} ({len(words)} words, {freq['len'].sum()} total letters)")
    print(f"Generated {trigrams_json} ({len(trigram_detail)} grids)")


if __name__ == "__main__":
    main()
