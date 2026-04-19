"""Per-word scoring functions for ranking ten-letter words.

Each scoring function takes a word and one or more baseline rate dicts and
returns a float. All functions are pure and side-effect-free. They handle
absent letters/bigrams/trigrams by treating their rate as 0 (via dict.get).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable


# ---- Scoring functions --------------------------------------------------------


def letter_score(word: str, letter_rates: dict[str, float]) -> float:
    """Sum baseline letter rates over the DISTINCT letters in `word`.

    Per DR2: repeated letters do not increase the score (hard cap at first
    occurrence). 'aaaaa' scores `letter_rates['a']`, not `5 * letter_rates['a']`.
    """
    return sum(letter_rates.get(letter, 0.0) for letter in set(word))


def bigram_score(word: str, bigram_rates: dict[str, float]) -> float:
    """Sum baseline bigram rates over the DISTINCT bigrams in `word`.

    Parallels `letter_score`'s distinct cap: repeated bigrams do not increase
    the score. 'statistics' has bigrams st, ta, at, ti, is, st, ti, ic, cs —
    distinct set is {st, ta, at, ti, is, ic, cs}, so seven rates are summed.
    """
    distinct_bigrams = {word[i : i + 2] for i in range(len(word) - 1)}
    return sum(bigram_rates.get(bg, 0.0) for bg in distinct_bigrams)


def trigram_score(
    word: str,
    start_rates: dict[str, float],
    end_rates: dict[str, float],
) -> float:
    """Sum the start-trigram rate and the end-trigram rate of `word`.

    Returns `start_rates[word[:3]] + end_rates[word[-3:]]`. Both terms are 0
    if the trigram is absent from its respective rate dict.

    Raises ValueError if len(word) < 3.
    """
    if len(word) < 3:
        raise ValueError(
            f"trigram_score requires len(word) >= 3, got {len(word)}: {word!r}"
        )
    return start_rates.get(word[:3], 0.0) + end_rates.get(word[-3:], 0.0)


def positional_endpoint_score(
    word: str,
    letter_rates: dict[str, float],
    first_rates: dict[str, float],
    last_rates: dict[str, float],
) -> float:
    """Letter-coverage score plus positional bonuses for start and end letters.

    Score = letter_score(word) + first_rates[word[0]] + last_rates[word[-1]].
    Rewards words that combine diverse common letters (via letter_score) with
    common positional endpoints — both terms count even when word[0] == word[-1].

    Raises ValueError on empty word.
    """
    if not word:
        raise ValueError("positional_endpoint_score requires a non-empty word")
    return (
        letter_score(word, letter_rates)
        + first_rates.get(word[0], 0.0)
        + last_rates.get(word[-1], 0.0)
    )


# ---- Generic top-N helper -----------------------------------------------------


def top_n_by_score(
    words: Iterable[str],
    score_fn: Callable[[str], float],
    n: int = 50,
) -> list[tuple[str, float]]:
    """Return the top-N (word, score) tuples, sorted descending by score.

    Tie-break: alphabetical by word (stable). The returned list has at most
    `n` entries; fewer if `words` has fewer than `n` distinct entries.

    `score_fn` must be a callable taking a single `word` argument and returning
    a float. Use `functools.partial` to bind baseline rate dicts:

        from functools import partial
        score = partial(letter_score, letter_rates=rates)
        top = top_n_by_score(words_10, score, n=50)
    """
    scored = [(word, score_fn(word)) for word in words]
    # Guard against NaN/inf — Python's Timsort is non-deterministic on NaN
    # tuples. Bad rate dicts (e.g., divide-by-zero upstream) surface here
    # rather than producing silently misordered rankings.
    for word, score in scored:
        if not math.isfinite(score):
            raise ValueError(
                f"score_fn returned non-finite value {score!r} for word {word!r}"
            )
    # Sort by (-score, word): higher score first, ties broken alphabetically.
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored[:n]
