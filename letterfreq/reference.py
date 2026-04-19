"""Baseline frequency counters over an arbitrary word corpus.

All functions are pure: input is an iterable of pre-cleaned lowercase words
(no validation here — the caller is responsible for filtering); output is a
plain dict. No I/O, no globals.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


def letter_counts(words: Iterable[str]) -> dict[str, int]:
    """Count occurrences of each letter across all words."""
    counter: Counter[str] = Counter()
    for word in words:
        counter.update(word)
    return dict(counter)


def bigram_counts(words: Iterable[str]) -> dict[str, int]:
    """Count consecutive two-letter sequences across all words.

    For each word, every adjacent letter pair contributes one count, including
    repeats (e.g., 'eel' contributes 'ee' and 'el').
    """
    counter: Counter[str] = Counter()
    for word in words:
        for i in range(len(word) - 1):
            counter[word[i : i + 2]] += 1
    return dict(counter)


def start_trigram_counts(
    words: Iterable[str], min_length: int = 4
) -> dict[str, int]:
    """Count the first three letters of each word of length >= min_length.

    Default min_length=4 (per DR3) avoids the 3-letter double-count where a
    3-letter word's start trigram and end trigram are identical.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if len(word) >= min_length:
            counter[word[:3]] += 1
    return dict(counter)


def end_trigram_counts(
    words: Iterable[str], min_length: int = 4
) -> dict[str, int]:
    """Count the last three letters of each word of length >= min_length.

    Default min_length=4 (per DR3) — see start_trigram_counts.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if len(word) >= min_length:
            counter[word[-3:]] += 1
    return dict(counter)


def first_letter_counts(words: Iterable[str]) -> dict[str, int]:
    """Count the first letter of each word.

    No minimum-length filter (per DR8) — every word in the baseline
    contributes its first letter exactly once.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if word:
            counter[word[0]] += 1
    return dict(counter)


def last_letter_counts(words: Iterable[str]) -> dict[str, int]:
    """Count the last letter of each word.

    No minimum-length filter (per DR8) — every word in the baseline
    contributes its last letter exactly once.
    """
    counter: Counter[str] = Counter()
    for word in words:
        if word:
            counter[word[-1]] += 1
    return dict(counter)


def to_rates(counts: dict[str, int], total: int) -> dict[str, float]:
    """Convert raw counts to per-occurrence rates.

    Rates are `count / total`. Caller chooses what `total` means (sum of
    counts, total word count, etc.). Returns 0.0 for any zero count.
    """
    if total <= 0:
        return {key: 0.0 for key in counts}
    return {key: value / total for key, value in counts.items()}
