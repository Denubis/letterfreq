"""Contract tests for main_ten.load_words."""

from __future__ import annotations

from pathlib import Path

from main_ten import load_words


def test_load_words_deduplicates_preserving_order(tmp_path: Path) -> None:
    p = tmp_path / "dups.txt"
    p.write_text("apple\nbanana\napple\ncherry\nbanana\napple\n")
    assert load_words(p) == ["apple", "banana", "cherry"]


def test_load_words_drops_empty_lines(tmp_path: Path) -> None:
    p = tmp_path / "spaced.txt"
    p.write_text("a\n\nb\n\n\nc\n")
    assert load_words(p) == ["a", "b", "c"]
