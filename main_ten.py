"""Generate docs/ten/index.md — the ten-letter analysis page.

Imperative shell only: reads pre-filtered corpus files, computes baseline
rates via letterfreq.reference, ranks ten-letter words via letterfreq.scoring,
renders HTML tables via letterfreq.render, and writes the composed Markdown
document. All side effects live here; pure logic lives in letterfreq/.
"""

from __future__ import annotations

from pathlib import Path

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
    """Read one-word-per-line corpus file; drop empty lines; dedupe (preserve order).

    Defensive dedupe via dict.fromkeys protects ranking from showing the same
    word twice if the corpus file contains duplicates (Phase 5 deferred
    concern #3; complementary uniqueness assertion lives in Phase 7).
    """
    return list(dict.fromkeys(w for w in path.read_text().splitlines() if w))


def _count_baseline(baseline: list[str]) -> dict[str, dict[str, int]]:
    """Compute all six baseline count dicts from the corpus.

    Returned keys: 'letter', 'bigram', 'start_trigram', 'end_trigram',
    'first_letter', 'last_letter'. Pure; suitable for direct testing.
    """
    return {
        "letter": letter_counts(baseline),
        "bigram": bigram_counts(baseline),
        "start_trigram": start_trigram_counts(baseline),  # default min_length=4
        "end_trigram": end_trigram_counts(baseline),
        "first_letter": first_letter_counts(baseline),
        "last_letter": last_letter_counts(baseline),
    }


def _compute_rates(
    counts: dict[str, dict[str, int]],
    word_total: int,
) -> dict[str, dict[str, float]]:
    """Convert count dicts into rate dicts using the production denominator choices.

    Per-occurrence rate (sum-of-counts denominator) for letter / bigram /
    start_trigram / end_trigram. Per-word rate (`word_total` denominator) for
    first_letter / last_letter (per DR8: every baseline word contributes
    exactly one first and one last letter).

    Each returned rate dict sums to 1.0 by construction. Factoring this out
    of generate_page lets tests assert the production-path denominator
    choices rather than re-deriving them in test setup (Phase 5 deferred
    concern #1; closes the regression-guard gap from Phase 2).
    """
    return {
        "letter": to_rates(counts["letter"], sum(counts["letter"].values())),
        "bigram": to_rates(counts["bigram"], sum(counts["bigram"].values())),
        # Trigram totals: only words of length >= 4 contributed (default
        # min_length=4 per DR3). Sum-of-counts equals the count of length-≥4
        # words. Critical: using `word_total` here would systematically
        # deflate trigram rates by the proportion of length-3 words.
        "start_trigram": to_rates(
            counts["start_trigram"], sum(counts["start_trigram"].values())
        ),
        "end_trigram": to_rates(
            counts["end_trigram"], sum(counts["end_trigram"].values())
        ),
        "first_letter": to_rates(counts["first_letter"], word_total),
        "last_letter": to_rates(counts["last_letter"], word_total),
    }


def generate_page(words_10: list[str], baseline: list[str]) -> str:
    """Compose the full docs/ten/index.md content."""
    # --- Counts and rates over baseline -----------------------------------
    counts = _count_baseline(baseline)
    word_total = len(baseline)
    rates = _compute_rates(counts, word_total)

    letter_c = counts["letter"]
    bigram_c = counts["bigram"]
    start_c = counts["start_trigram"]
    end_c = counts["end_trigram"]
    first_c = counts["first_letter"]
    last_c = counts["last_letter"]

    letter_r = rates["letter"]
    bigram_r = rates["bigram"]
    start_r = rates["start_trigram"]
    end_r = rates["end_trigram"]
    first_r = rates["first_letter"]
    last_r = rates["last_letter"]

    # trigram_word_total only used as the `word_count` argument to
    # render_trigram_pair (drives its "Per word" column).
    trigram_word_total = sum(start_c.values())  # == sum(end_c.values())

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
    rank_letter = render_letter_ranking(words_10, letter_r, top_n=50)
    rank_bigram = render_bigram_ranking(words_10, bigram_r, top_n=50)
    rank_trigram = render_trigram_ranking(words_10, start_r, end_r, top_n=50)
    rank_positional = render_positional_ranking(words_10, first_r, last_r, top_n=50)

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
        "Note: the reference tables above show **per-word rates** (fraction "
        "of baseline words containing each item). The scoring formulas below "
        "use **per-occurrence rates** (fraction of all letter / bigram / "
        "trigram occurrences across the baseline). Same baseline corpus, "
        "different denominators — so a letter like `e` appears with two "
        "different numbers across the page. Both are correct for their "
        "respective question.\n\n"
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
