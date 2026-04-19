"""Tests for letterfreq.grouping — gap clustering and dict-aware bucket helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from letterfreq.grouping import (
    GAP_EPSILON,
    exemplar,
    gap_cluster,
    load_us_dict,
    sort_bucket_words,
)


# ---- gap_cluster --------------------------------------------------------------


def test_gap_cluster_empty_input_returns_empty() -> None:
    assert gap_cluster([], eps=0.01) == []


def test_gap_cluster_single_word_single_bucket() -> None:
    assert gap_cluster([("foo", 0.5)], eps=0.01) == [[("foo", 0.5)]]


def test_gap_cluster_exact_ties_collapse_regardless_of_eps() -> None:
    scored = [("a", 0.5), ("b", 0.5), ("c", 0.3)]
    buckets = gap_cluster(scored, eps=0.0)
    assert buckets == [[("a", 0.5), ("b", 0.5)], [("c", 0.3)]]


def test_gap_cluster_near_ties_collapse_within_eps() -> None:
    # 0.5068 and 0.5066 differ by 0.0002 — within eps=0.0005
    scored = [("a", 0.5068), ("b", 0.5066), ("c", 0.5050)]
    buckets = gap_cluster(scored, eps=0.0005)
    # a and b cluster (gap 0.0002); c splits (gap 0.0016 > 0.0005)
    assert [[w for w, _ in b] for b in buckets] == [["a", "b"], ["c"]]


def test_gap_cluster_chain_through_transitive_gaps() -> None:
    """Successive small gaps chain — clustering is relative to previous, not first."""
    scored = [("a", 1.000), ("b", 0.9996), ("c", 0.9992), ("d", 0.9988)]
    buckets = gap_cluster(scored, eps=0.0005)
    # Each gap is 0.0004 < eps, so all four chain into one bucket despite
    # a→d gap of 0.0012 > eps. This is intentional for descent-through-plateau.
    assert len(buckets) == 1
    assert [w for w, _ in buckets[0]] == ["a", "b", "c", "d"]


def test_gap_cluster_gap_exactly_at_eps_collapses() -> None:
    # Boundary: exactly-eps gap is included in the current bucket (≤ not <).
    scored = [("a", 0.5000), ("b", 0.4999)]
    buckets = gap_cluster(scored, eps=0.0001)
    assert len(buckets) == 1


def test_gap_cluster_default_epsilon_is_one_ten_thousandth() -> None:
    assert GAP_EPSILON == pytest.approx(1e-4)


# ---- load_us_dict -------------------------------------------------------------


def test_load_us_dict_returns_empty_for_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.txt"
    assert load_us_dict(missing) == frozenset()


def test_load_us_dict_strips_capitalised_and_possessive(tmp_path: Path) -> None:
    p = tmp_path / "dict.txt"
    p.write_text("apple\nBanana\ncat's\ndog\n\nEagle\n")
    result = load_us_dict(p)
    assert result == frozenset({"apple", "dog"})


def test_load_us_dict_is_frozenset(tmp_path: Path) -> None:
    p = tmp_path / "dict.txt"
    p.write_text("apple\n")
    result = load_us_dict(p)
    assert isinstance(result, frozenset)


# ---- sort_bucket_words --------------------------------------------------------


def test_sort_bucket_words_dict_first_alphabetical_within_groups() -> None:
    us_dict = frozenset({"apple", "dog", "cat"})
    words = ["zebra", "apple", "yak", "dog", "cat", "ox"]
    result = sort_bucket_words(words, us_dict)
    assert result == [
        ("apple", True),
        ("cat", True),
        ("dog", True),
        ("ox", False),
        ("yak", False),
        ("zebra", False),
    ]


def test_sort_bucket_words_all_dict_resident() -> None:
    us_dict = frozenset({"b", "a", "c"})
    assert sort_bucket_words(["c", "a", "b"], us_dict) == [
        ("a", True), ("b", True), ("c", True),
    ]


def test_sort_bucket_words_none_dict_resident() -> None:
    assert sort_bucket_words(["c", "a", "b"], frozenset()) == [
        ("a", False), ("b", False), ("c", False),
    ]


def test_sort_bucket_words_empty() -> None:
    assert sort_bucket_words([], frozenset()) == []


# ---- exemplar -----------------------------------------------------------------


def test_exemplar_picks_first_dict_resident_alphabetically() -> None:
    us_dict = frozenset({"preambling", "predicting"})
    words = ["preallying", "preambling", "prebidding", "predicting"]
    # preallying is alphabetically first overall but not in dict;
    # preambling is first alphabetically among the in-dict subset.
    assert exemplar(words, us_dict) == "preambling"


def test_exemplar_falls_back_to_first_alphabetical_when_bucket_all_obscure() -> None:
    words = ["zebra", "aardvark", "mongoose"]
    # None in dict → strict alphabetical
    assert exemplar(words, frozenset()) == "aardvark"


def test_exemplar_single_word() -> None:
    assert exemplar(["predations"], frozenset()) == "predations"
    assert exemplar(["predations"], frozenset({"predations"})) == "predations"


def test_exemplar_raises_on_empty() -> None:
    with pytest.raises(ValueError, match="at least one"):
        exemplar([], frozenset())
