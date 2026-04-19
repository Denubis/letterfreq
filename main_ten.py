"""Generate docs/ten/index.md — the ten-letter analysis page.

Imperative shell only: reads pre-filtered corpus files, computes baseline
rates via letterfreq.reference, ranks ten-letter words via letterfreq.scoring,
renders HTML tables via letterfreq.render, and writes the composed Markdown
document. All side effects live here; pure logic lives in letterfreq/.
"""

from __future__ import annotations

from pathlib import Path

from letterfreq.grouping import load_us_dict
from letterfreq.reference import (
    bigram_counts,
    end_trigram_counts,
    first_letter_counts,
    last_letter_counts,
    letter_counts,
    start_trigram_counts,
    to_rates,
)
from letterfreq.render import (
    render_bigram_ranking,
    render_bigram_table,
    render_first_last_pair,
    render_letter_ranking,
    render_letter_table,
    render_positional_ranking,
    render_trigram_pair,
    render_trigram_ranking,
)

REPO_ROOT = Path(__file__).parent
DATA_DIR = REPO_ROOT / "data"
WORDS_10_FILE = DATA_DIR / "words_10.txt"
BASELINE_FILE = DATA_DIR / "words_3_to_10.txt"
INDEX_MD = REPO_ROOT / "docs" / "ten" / "index.md"


def load_words(path: Path) -> list[str]:
    """Read one-word-per-line corpus file; drop empty lines; dedupe (preserve order)."""
    return list(dict.fromkeys(w for w in path.read_text().splitlines() if w))


def generate_page(words_10: list[str], baseline: list[str]) -> str:
    """Compose the full docs/ten/index.md content."""
    letter_c = letter_counts(baseline)
    bigram_c = bigram_counts(baseline)
    start_c = start_trigram_counts(baseline)
    end_c = end_trigram_counts(baseline)
    first_c = first_letter_counts(baseline)
    last_c = last_letter_counts(baseline)

    word_total = len(baseline)
    trigram_word_total = sum(start_c.values())

    letter_r = to_rates(letter_c, sum(letter_c.values()))
    bigram_r = to_rates(bigram_c, sum(bigram_c.values()))
    start_r = to_rates(start_c, trigram_word_total)
    end_r = to_rates(end_c, sum(end_c.values()))
    first_r = to_rates(first_c, word_total)
    last_r = to_rates(last_c, word_total)

    # --- Reference tables --------------------------------------------------
    # The `word_count` argument to each renderer drives the "Per word" rate
    # column displayed in the table. We use:
    #   - `word_total` (full baseline) for letter, bigram, first/last tables
    #     because every baseline word contributed to those counts.
    #   - `trigram_word_total` (length-≥4 words only) for the trigram pair so
    #     the displayed rate matches the population that actually contributed
    #     to the count, consistent with start_r / end_r above.
    ref_letter = render_letter_table(letter_r, letter_c, word_total)
    ref_bigram = render_bigram_table(bigram_r, bigram_c, word_total, top_n=100)
    ref_trigram = render_trigram_pair(
        start_r, start_c, end_r, end_c, trigram_word_total, top_n=50
    )
    ref_first_last = render_first_last_pair(
        first_r, first_c, last_r, last_c, word_total
    )

    # --- Ranking tables (over the 10-letter words) -------------------------
    # US spelling dict drives the exemplar cascade and dict-resident marking
    # in the expansion panel. Falls back to alphabetical when unavailable.
    us_dict = load_us_dict()
    rank_letter = render_letter_ranking(words_10, letter_r, top_n=50, us_dict=us_dict)
    rank_bigram = render_bigram_ranking(words_10, bigram_r, top_n=50, us_dict=us_dict)
    rank_trigram = render_trigram_ranking(
        words_10, start_r, end_r, top_n=50, us_dict=us_dict
    )
    rank_positional = render_positional_ranking(
        words_10, letter_r, first_r, last_r, top_n=50, us_dict=us_dict
    )

    return (
        "---\n"
        "icon: null\n"
        "---\n\n"
        "# Ten-Letter Word Frequencies\n\n"
        f"Reference frequencies computed over **{word_total:,}** English words "
        f"of length 3–10 (the baseline corpus). Rankings cover **{len(words_10):,}** "
        f"ten-letter words. All tables sortable by clicking column headers.\n\n"
        "## Baseline frequencies\n\n"
        "### Letter frequency\n\n"
        f"{ref_letter}\n\n"
        "### Bigram frequency (top 100)\n\n"
        f"{ref_bigram}\n\n"
        "### Start and end trigrams (top 50 each)\n\n"
        f"{ref_trigram}\n\n"
        "### First and last letters\n\n"
        f"{ref_first_last}\n\n"
        "## Ten-letter words\n\n"
        "### Top 50 by letter coverage\n\n"
        "Score = sum of baseline rates over the **distinct** letters in the word. "
        "Words that pack many high-frequency letters score highest; repeats add "
        "nothing.\n\n"
        f"{rank_letter}\n\n"
        "### Top 50 by bigram score\n\n"
        "Score = sum of baseline bigram rates over the 9 consecutive bigram "
        "positions. Repeated bigrams contribute each time they occur.\n\n"
        f"{rank_bigram}\n\n"
        "### Top 50 by start + end trigram\n\n"
        "Score = baseline rate of the word's start trigram (positions 1–3) + "
        "baseline rate of the word's end trigram (positions 8–10).\n\n"
        f"{rank_trigram}\n\n"
        "### Top 50 by positional first + last letter\n\n"
        "Score = baseline rate of the word's first letter + baseline rate of "
        "the word's last letter. Both contribute even when they're the same "
        "letter (no distinct cap).\n\n"
        f"{rank_positional}\n"
    )


def main() -> None:
    words_10 = load_words(WORDS_10_FILE)
    baseline = load_words(BASELINE_FILE)
    page = generate_page(words_10, baseline)
    INDEX_MD.parent.mkdir(parents=True, exist_ok=True)
    INDEX_MD.write_text(page)
    print(
        f"Generated {INDEX_MD} "
        f"({len(words_10):,} ten-letter words, {len(baseline):,} baseline words)"
    )


if __name__ == "__main__":
    main()
