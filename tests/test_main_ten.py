"""Production-path tests for main_ten.generate_page and its helpers.

Closes three Phase 5 deferred concerns:
  1. Rate dicts produced by _compute_rates sum to 1.0 (denominator regression
     guard — calls the production helper, not a re-derivation).
  2. load_words deduplicates input lines.
  3. Top-N bigram transparency covers ≥50% of total score for every top-10
     ranked word, where N is the production cap BIGRAM_TRANSPARENCY_CAP from
     letterfreq.render. Single source of truth: bumping the constant in
     render.py changes both the rendered cell width and what this test asserts.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from letterfreq.render import BIGRAM_TRANSPARENCY_CAP
from letterfreq.scoring import bigram_score, top_n_by_score
from main_ten import (
    WORDS_10_FILE,
    _compute_rates,
    _count_baseline,
    load_words,
)

BASELINE_PATH = Path(__file__).parent.parent / "data" / "words_3_to_10.txt"


@pytest.fixture(scope="module")
def baseline_words() -> list[str]:
    if not BASELINE_PATH.exists():
        pytest.skip(f"baseline corpus not present: {BASELINE_PATH}")
    return [w for w in BASELINE_PATH.read_text().splitlines() if w]


@pytest.fixture(scope="module")
def production_rates(baseline_words: list[str]) -> dict[str, dict[str, float]]:
    """The exact rate dicts generate_page consumes, via the production helper."""
    return _compute_rates(_count_baseline(baseline_words), len(baseline_words))


# --- Concern #1: rate dicts sum to 1.0 (production path) -----------------------


@pytest.mark.parametrize(
    "key",
    [
        "letter",
        "bigram",
        "start_trigram",
        "end_trigram",
        "first_letter",
        "last_letter",
    ],
)
def test_production_rates_sum_to_one(
    production_rates: dict[str, dict[str, float]], key: str
) -> None:
    """Regression guard: every rate dict generate_page uses must sum to 1.0.

    The classic denominator bug surfaced during plan review was using
    `len(baseline)` instead of `sum(start_trigram_counts.values())` for the
    trigram rate, which would systematically deflate trigram rates by the
    proportion of length-3 words. This parametrised test catches any future
    occurrence by exercising the production helper directly.
    """
    rates = production_rates[key]
    assert sum(rates.values()) == pytest.approx(1.0, rel=1e-9), (
        f"{key} rates sum to {sum(rates.values())!r}, not 1.0 — "
        "denominator choice in _compute_rates is wrong."
    )


# --- Concern #3: load_words deduplicates --------------------------------------


def test_load_words_deduplicates_preserving_order(tmp_path: Path) -> None:
    """If the corpus file ever contains duplicates, ranking must not show the
    same word twice. Order of first occurrence is preserved.
    """
    p = tmp_path / "dups.txt"
    p.write_text("apple\nbanana\napple\ncherry\nbanana\napple\n")
    assert load_words(p) == ["apple", "banana", "cherry"]


def test_load_words_drops_empty_lines(tmp_path: Path) -> None:
    p = tmp_path / "spaced.txt"
    p.write_text("a\n\nb\n\n\nc\n")
    assert load_words(p) == ["a", "b", "c"]


# --- Concern #2: bigram top-3 transparency covers majority --------------------


def test_topN_bigram_transparency_covers_majority(
    baseline_words: list[str],
    production_rates: dict[str, dict[str, float]],
) -> None:
    """For every top-10 ranked ten-letter word, the top-N bigram contributions
    must sum to ≥50% of that word's total bigram score, where
    N = letterfreq.render.BIGRAM_TRANSPARENCY_CAP (the same cap the rendered
    "Top contributors" cell uses). If this fails, bump the constant in
    letterfreq/render.py and re-render — the test will pick up the new value
    automatically because it imports the constant rather than hard-coding it.
    """
    if not WORDS_10_FILE.exists():
        pytest.skip(f"ten-letter corpus not present: {WORDS_10_FILE}")
    words_10 = load_words(WORDS_10_FILE)
    bigram_r = production_rates["bigram"]
    cap = BIGRAM_TRANSPARENCY_CAP

    def score(word: str) -> float:
        return bigram_score(word, bigram_r)

    top10 = top_n_by_score(words_10, score, n=10)
    failures: list[str] = []
    for word, total in top10:
        if total <= 0:
            continue  # nothing to attribute
        per_word_bigrams = Counter(word[i : i + 2] for i in range(len(word) - 1))
        contribs = sorted(
            (bigram_r.get(bg, 0.0) * cnt for bg, cnt in per_word_bigrams.items()),
            reverse=True,
        )
        topN_sum = sum(contribs[:cap])
        ratio = topN_sum / total
        if ratio < 0.5:
            failures.append(
                f"  {word!r}: top-{cap} covers {ratio:.1%} "
                f"({topN_sum:.4f} / {total:.4f})"
            )
    assert not failures, (
        f"Top-{cap} bigram transparency hides more than half of the score for "
        "the following top-10 ranked words. Bump BIGRAM_TRANSPARENCY_CAP in "
        "letterfreq/render.py (e.g., from 3 to 5) and re-run main_ten.py + "
        "zensical build. The test re-reads the constant on next run.\n"
        + "\n".join(failures)
    )
