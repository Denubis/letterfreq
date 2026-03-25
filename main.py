"""Compute overall letter frequencies from five-letter English words and generate docs/index.md."""

from __future__ import annotations

import re
import string
from pathlib import Path

import polars as pl

WORD_FILE = Path("/usr/share/dict/words")
DOCS_DIR = Path(__file__).parent / "docs"
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


def generate_page(words: list[str], freq: pl.DataFrame) -> str:
    """Generate the full docs/index.md content."""
    word_count = len(words)
    table_html = generate_frequency_table_html(freq, word_count)
    unigrams = compute_positional_unigrams(words)
    heatmap_html = generate_heatmap_html(unigrams)

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
        f"{heatmap_html}\n"
    )


def main() -> None:
    words = load_words()
    freq = compute_overall_frequencies(words)
    page = generate_page(words, freq)
    INDEX_MD.parent.mkdir(parents=True, exist_ok=True)
    INDEX_MD.write_text(page)
    print(f"Generated {INDEX_MD} ({len(words)} words, {freq['len'].sum()} total letters)")


if __name__ == "__main__":
    main()
