"""Gap-based clustering of ranked scores and dictionary-aware bucket sorting.

Ten-letter ranking tables are noisy when displayed flat: high-scoring words
crowd together as near-duplicates (anagram tiers, `pre___ing` patterns) that
all share the same feature set. These helpers collapse near-ties into buckets
and order words within a bucket so recognisable forms surface first.

All functions are pure: no file I/O except `load_us_dict`, which reads a
system spelling dictionary exactly once per call.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


GAP_EPSILON = 1e-4
"""Default gap threshold: scores within 0.0001 collapse into one bucket."""


US_DICT_PATH = Path("/usr/share/dict/american-english")
"""System-provided US English word list on Debian/Ubuntu (wamerican package)."""


def gap_cluster(
    scored_desc: list[tuple[str, float]],
    eps: float = GAP_EPSILON,
) -> list[list[tuple[str, float]]]:
    """Cluster a descending-sorted (word, score) list into gap-bounded buckets.

    Walks the list in order, starting a new bucket whenever the score gap to
    the previous word exceeds `eps`. Bucket boundaries therefore reflect
    *local* discontinuities in the score distribution, not fixed rounding
    boundaries — .7068 and .7066 cluster together even though rounding to 2dp
    would put them in different buckets (.71 vs .71, but .7068 and .7049 would
    split only at the .003 gap, not at rounding boundaries).

    `scored_desc` MUST already be sorted by score descending; this function
    does not sort. An empty input returns an empty list.
    """
    if not scored_desc:
        return []
    buckets: list[list[tuple[str, float]]] = [[scored_desc[0]]]
    for word, score in scored_desc[1:]:
        prev_score = buckets[-1][-1][1]
        if (prev_score - score) <= eps:
            buckets[-1].append((word, score))
        else:
            buckets.append([(word, score)])
    return buckets


def load_us_dict(path: Path = US_DICT_PATH) -> frozenset[str]:
    """Load the US English spelling list as a frozenset of lowercase-alpha words.

    Strips possessives (word's → dropped) and proper nouns (Capitalised → dropped)
    so only canonical lowercase common words remain. On Debian/Ubuntu the default
    path is `/usr/share/dict/american-english` (provided by the wamerican package).

    Returns an empty set if the file does not exist — callers should treat an
    empty set as "dict unavailable", where every word is non-resident and the
    cascade falls through to pure alphabetical order.
    """
    if not path.exists():
        return frozenset()
    return frozenset(
        word for word in path.read_text().splitlines()
        if word and word.isalpha() and word.islower()
    )


def sort_bucket_words(
    words: Iterable[str],
    us_dict: frozenset[str],
) -> list[tuple[str, bool]]:
    """Sort a bucket's words dict-resident-first, alphabetical within each group.

    Returns a list of (word, is_dict_resident) pairs. Words in the US dict
    come first (alphabetically), then non-dict words (alphabetically). The
    boolean lets callers visually mark dict-resident entries in the rendered
    expansion panel.
    """
    in_dict: list[str] = []
    out_of_dict: list[str] = []
    for word in words:
        if word in us_dict:
            in_dict.append(word)
        else:
            out_of_dict.append(word)
    in_dict.sort()
    out_of_dict.sort()
    return [(w, True) for w in in_dict] + [(w, False) for w in out_of_dict]


def exemplar(words: Iterable[str], us_dict: frozenset[str]) -> str:
    """Return the first dict-resident word alphabetically, or first alphabetically.

    Used as the visible row when a bucket collapses multiple tied words into
    a single table entry. The cascade means recognisable forms (e.g. `preambling`)
    surface as the exemplar rather than alphabetically-earliest obscurities
    (e.g. `preallying`), except when an entire bucket is non-dict, in which
    case the bucket is all-obscure anyway and alphabetical order is the best
    deterministic choice.

    Raises ValueError on empty input.
    """
    word_list = list(words)
    if not word_list:
        raise ValueError("exemplar requires at least one word")
    in_dict_sorted = sorted(w for w in word_list if w in us_dict)
    if in_dict_sorted:
        return in_dict_sorted[0]
    return sorted(word_list)[0]
