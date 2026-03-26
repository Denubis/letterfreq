"""Shared pytest fixtures for letterfreq tests."""

from __future__ import annotations

import pytest

from main import load_words


@pytest.fixture(scope="session")
def words() -> list[str]:
    return load_words()


@pytest.fixture(scope="session")
def word_count(words: list[str]) -> int:
    return len(words)
