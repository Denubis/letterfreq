"""Download dwyl/english-words and write per-page word files.

One-shot helper. Outputs are committed; this script is not run during
normal builds. Re-run when upstream changes or when corpus filter
criteria change.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
SOURCE_URL = (
    "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
)
ALPHA_LOWER = re.compile(r"^[a-z]+$")


def fetch_words() -> list[str]:
    """Download the upstream alpha-only word list and return cleaned lowercase entries."""
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        raw = response.read().decode("utf-8")
    cleaned: list[str] = []
    for line in raw.splitlines():
        word = line.strip().lower()
        if ALPHA_LOWER.fullmatch(word):
            cleaned.append(word)
    return cleaned


def write_filtered(words: list[str], out_path: Path, min_len: int, max_len: int) -> int:
    """Write the subset of `words` whose length is in [min_len, max_len] inclusive."""
    # words_alpha.txt is already deduplicated upstream; list comprehension suffices.
    selected = sorted(w for w in words if min_len <= len(w) <= max_len)
    out_path.write_text("\n".join(selected) + "\n")
    return len(selected)


def main() -> None:
    words = fetch_words()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    n10 = write_filtered(words, DATA_DIR / "words_10.txt", 10, 10)
    n3to10 = write_filtered(words, DATA_DIR / "words_3_to_10.txt", 3, 10)

    print(f"words_10.txt:        {n10:>7,} entries")
    print(f"words_3_to_10.txt:   {n3to10:>7,} entries")
    print("data/words.txt left untouched (existing 5-letter corpus).")


if __name__ == "__main__":
    main()
