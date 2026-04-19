# Ten-Letter Page Implementation Plan — Phase 1: Corpus generation and site restructuring

**Goal:** Generate the two new corpus files (`data/words_10.txt`, `data/words_3_to_10.txt`); restructure the existing site so the five-letter page lives at `/five/` and a landing page at `/`; bump Zensical to >=0.0.33.

**Architecture:** Infrastructure-only phase. Adds a one-shot helper script (`scripts/build_corpora.py`) that downloads the dwyl/english-words list and emits two pre-filtered files. Moves the existing `docs/index.md` and its co-located JSON data to `docs/five/`. Creates an empty `docs/ten/` placeholder and a small `docs/index.md` landing page. Updates `main.py` output paths and `zensical.toml` (explicit `nav` block, refreshed site title/description), and bumps the Zensical pin in `pyproject.toml`.

**Tech Stack:** Python 3.14+, uv 0.5+, Zensical >=0.0.33, urllib (stdlib).

**Scope:** Phase 1 of 7 from `/home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md`.

**Codebase verified:** 2026-04-19 (full sweep — see investigation report in conversation context). Key findings:
- main.py constants: `WORD_FILE = data/words.txt`, `DOCS_DIR = docs`, `DATA_DIR = docs/data`, `INDEX_MD = docs/index.md`. `main()` writes only to INDEX_MD.
- JS fetch paths confirmed bare-relative: `sort-tables.js:39` `fetch("data/bigrams.json")`, `trigram-expand.js:8` `fetch("data/trigrams.json")`.
- `zensical.toml`: no active `nav` block (commented-out lines 47–50); current `site_name = "Five-Letter Word Frequencies"`.
- `pyproject.toml`: `zensical>=0.0.28`.
- `data/words.txt`: 15,921 lines.
- `tests/conftest.py` uses `load_words()` from `main.py` which reads `WORD_FILE = data/words.txt` — unchanged by Phase 1.
- ABSENT: `letterfreq/`, `main_ten.py`, `scripts/`, `data/words_10.txt`, `data/words_3_to_10.txt`, `docs/five/`, `docs/ten/`.

**Phase Type:** infrastructure

---

## Acceptance Criteria Coverage

This phase implements infrastructure — no functional ACs. Verifies operationally per design plan's Done-when:

- **ten-letter-page.AC7.1 Success:** `uv run zensical build --clean` succeeds with `zensical>=0.0.33`.
- **ten-letter-page.AC7.2 Success:** `/five/` renders with bigram drill-downs and trigram expansions still working (manual visual check).
- **ten-letter-page.AC7.3 Success:** `/` shows the landing page with links to `/five/` and `/ten/`.
- **ten-letter-page.AC7.4 Success:** `zensical.toml` `nav` block exposes Home, Five-letter, Ten-letter.
- **ten-letter-page.AC7.5 Success:** Dark/light toggle and `navigation.instant` behave on both pages.
- **ten-letter-page.AC8.1 Success:** `data/words_10.txt` is non-empty; every line matches `^[a-z]{10}$`.
- **ten-letter-page.AC8.2 Success:** `data/words_3_to_10.txt` is non-empty; every line matches `^[a-z]{3,10}$`.
- **ten-letter-page.AC8.3 Success:** `data/words.txt` (existing 5-letter) is unchanged: line count ≥ 15,000, every line matches `^[a-z]{5}$`.

Functional ACs (AC1–AC6, AC10) are covered by Phases 2–6. Documentation ACs (AC9) are covered by Phase 7. Tests for AC8 invariants are written in Phase 7.

---

## Implementation Tasks

<!-- START_TASK_0 -->
### Task 0: Tag the pre-implementation state on `main` (rollback boundary)

**No file changes — git operation only.**

The user chose to implement directly on `main` rather than on a feature branch (recorded during workspace setup). To preserve a single-command rollback in case Phase 5 (or any later phase) reveals an architectural problem that requires re-doing several phases' work, tag the current `main` HEAD before any phase commits land:

```bash
git tag pre-ten-letter-page
git tag --list pre-ten-letter-page  # confirm tag exists
```

To roll back to this state at any point during execution:

```bash
# DESTRUCTIVE — only if you're sure
git reset --hard pre-ten-letter-page
```

To delete the tag after implementation completes successfully (optional, keeps it as a milestone marker if desired):

```bash
git tag -d pre-ten-letter-page  # only if you no longer want the marker
```

**Verification:** `git tag --list | grep pre-ten-letter-page` returns the tag.

**No commit** — tags do not produce commits.
<!-- END_TASK_0 -->

<!-- START_TASK_1 -->
### Task 1: Create `scripts/build_corpora.py` helper

**Files:**
- Create: `/home/brian/llm/letterfreq/scripts/__init__.py` (empty)
- Create: `/home/brian/llm/letterfreq/scripts/build_corpora.py`

**Implementation:**

```python
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
    with urllib.request.urlopen(SOURCE_URL) as response:
        raw = response.read().decode("utf-8")
    cleaned: list[str] = []
    for line in raw.splitlines():
        word = line.strip().lower()
        if ALPHA_LOWER.fullmatch(word):
            cleaned.append(word)
    return cleaned


def write_filtered(words: list[str], out_path: Path, min_len: int, max_len: int) -> int:
    """Write the subset of `words` whose length is in [min_len, max_len] inclusive."""
    selected = sorted({w for w in words if min_len <= len(w) <= max_len})
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
```

**Verification:**

Run: `uv run python scripts/build_corpora.py`

Expected output (approximate counts will depend on the upstream snapshot):
```
words_10.txt:         ~30,000 entries
words_3_to_10.txt:   ~250,000 entries
data/words.txt left untouched (existing 5-letter corpus).
```

Confirm:
- `data/words_10.txt` exists, non-empty, all lines exactly 10 chars a–z.
- `data/words_3_to_10.txt` exists, non-empty, all lines 3–10 chars a–z.
- `data/words.txt` is unchanged: `git diff data/words.txt` shows no diff.

Sanity-check first/last lines of each new file:
```bash
head -3 data/words_10.txt
tail -3 data/words_10.txt
head -3 data/words_3_to_10.txt
tail -3 data/words_3_to_10.txt
```

**Commit:**

```bash
git add scripts/__init__.py scripts/build_corpora.py data/words_10.txt data/words_3_to_10.txt
git commit -m "feat: add scripts/build_corpora.py and generated corpora for ten-letter page"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Move `docs/index.md` and `docs/data/` under `docs/five/`

**Files:**
- Move: `/home/brian/llm/letterfreq/docs/index.md` → `/home/brian/llm/letterfreq/docs/five/index.md`
- Move: `/home/brian/llm/letterfreq/docs/data/bigrams.json` → `/home/brian/llm/letterfreq/docs/five/data/bigrams.json`
- Move: `/home/brian/llm/letterfreq/docs/data/trigrams.json` → `/home/brian/llm/letterfreq/docs/five/data/trigrams.json`
- Modify: `/home/brian/llm/letterfreq/main.py` lines 12–14 (path constants).

**Implementation:**

```bash
mkdir -p docs/five/data
git mv docs/index.md docs/five/index.md
git mv docs/data/bigrams.json docs/five/data/bigrams.json
git mv docs/data/trigrams.json docs/five/data/trigrams.json
# Now-empty docs/data/ should not exist (git mv on the only files in it should leave the dir gone, but verify)
[ -d docs/data ] && rmdir docs/data || true
```

In `main.py`, replace lines 12–14:

```python
DOCS_DIR = Path(__file__).parent / "docs"
DATA_DIR = DOCS_DIR / "data"
INDEX_MD = DOCS_DIR / "index.md"
```

with:

```python
DOCS_DIR = Path(__file__).parent / "docs"
FIVE_DIR = DOCS_DIR / "five"
DATA_DIR = FIVE_DIR / "data"
INDEX_MD = FIVE_DIR / "index.md"
```

**Verification:**

Re-generate the five-letter page from scratch:

```bash
uv run python main.py
```

Expected output (final line):
```
Generated /home/brian/llm/letterfreq/docs/five/index.md (15921 words, 79605 total letters)
```

Confirm `docs/five/index.md` regenerated, `docs/five/data/bigrams.json` and `docs/five/data/trigrams.json` regenerated identically (modulo dict ordering — JSON `sort_keys=True` is set in main.py:454).

Run existing tests to confirm `tests/conftest.py`'s `load_words()` import still works (`load_words` reads `WORD_FILE = data/words.txt` which is unchanged by this task):

```bash
uv run pytest -q
```

Expected: all existing tests pass.

**Commit:**

```bash
git add main.py docs/five/
git commit -m "refactor: move five-letter page output to docs/five/ subdirectory"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Create landing page (`docs/index.md`) and ten-letter placeholder (`docs/ten/index.md`)

**Files:**
- Create: `/home/brian/llm/letterfreq/docs/index.md`
- Create: `/home/brian/llm/letterfreq/docs/ten/index.md`

**Implementation:**

`docs/index.md` (landing):

```markdown
---
icon: null
---

# English Letter Frequencies

Letter, bigram, and trigram frequency analyses of English words from the
[dwyl/english-words](https://github.com/dwyl/english-words) corpus (Unlicense).

## Analyses

- **[Five-letter words](five/)** — Positional unigram, bigram, and trigram heatmaps for the 15,921 five-letter English words. Includes click-to-drill-down on every cell.
- **[Ten-letter words](ten/)** — Reference frequency tables (letter, bigram, start/end trigram, first/last letter) for the 3–10 letter baseline corpus, plus four top-50 rankings of ten-letter words by letter-coverage, bigram, start+end trigram, and positional first+last scores.

## Source

Corpus: [dwyl/english-words](https://github.com/dwyl/english-words) (Unlicense).

<!-- TODO: confirm the canonical GitHub URL for this repo and add a "Code:" link here. -->

```

`docs/ten/index.md` (placeholder; will be regenerated by `main_ten.py` in Phase 6):

```markdown
---
icon: null
---

# Ten-Letter Word Frequencies

*(Generated by `main_ten.py` — placeholder, content arrives in Phase 6.)*
```

**Verification:**

Confirm both files exist and contain the expected text.

**Commit:**

```bash
git add docs/index.md docs/ten/index.md
git commit -m "feat: add landing page and ten-letter placeholder"
```
<!-- END_TASK_3 -->

<!-- START_TASK_4 -->
### Task 4: Update `zensical.toml` (explicit `nav`, refreshed title/description)

**Files:**
- Modify: `/home/brian/llm/letterfreq/zensical.toml` lines 14, 20, and around line 47 (the commented-out `nav` example).

**Implementation:**

Replace line 14:
```
site_name = "Five-Letter Word Frequencies"
```
with:
```
site_name = "English Letter Frequencies"
```

Replace line 20:
```
site_description = "Positional letter, bigram, and trigram frequencies in five-letter English words"
```
with:
```
site_description = "Letter, bigram, and trigram frequencies for five- and ten-letter English words"
```

Replace the commented-out `nav` block (lines 47–50, currently `# nav = [\n# { "Get started" = "index.md" },\n# { "Markdown in 5min" = "markdown.md" },\n# ]`) with an active block:

```toml
nav = [
  { "Home" = "index.md" },
  { "Five-letter" = "five/index.md" },
  { "Ten-letter" = "ten/index.md" },
]
```

Leave all other settings unchanged.

**Verification:**

Spot-check by running:

```bash
uv run zensical build --clean 2>&1 | head -20
```

Expected build log lines include:
```
+ /
+ /five/
+ /ten/
```

(Order may vary.) The build must NOT include any `dev_docs/` URLs (we already verified earlier in this session that `dev_docs/` is correctly outside `docs_dir`).

**Commit:**

```bash
git add zensical.toml
git commit -m "feat: zensical.toml — explicit nav, refreshed site title/description"
```
<!-- END_TASK_4 -->

<!-- START_TASK_5 -->
### Task 5: Bump Zensical pin in `pyproject.toml` and refresh lockfile

**Files:**
- Modify: `/home/brian/llm/letterfreq/pyproject.toml` line 9.
- Auto-modified: `/home/brian/llm/letterfreq/uv.lock` (regenerated by `uv lock`).

**Implementation:**

Replace line 9:
```
    "zensical>=0.0.28",
```
with:
```
    "zensical>=0.0.33",
```

Then refresh the lockfile and sync:

```bash
uv lock
uv sync
```

**Verification:**

Confirm Zensical resolved to >=0.0.33:

```bash
uv pip list | grep -i zensical
```

Expected: `zensical 0.0.33` (or later).

Confirm the existing five-letter page still builds and renders:

```bash
uv run python main.py
uv run zensical build --clean
```

Expected: build succeeds. Spot-check `site/five/index.html` exists and contains the expected sortable table HTML. Spot-check `site/five/data/bigrams.json` and `site/five/data/trigrams.json` exist (Zensical copies non-Markdown files through).

Open `site/five/index.html` in a browser (or `uv run zensical serve`) and confirm:
- Sortable column headers respond to click.
- Clicking a bigram cell shows the drill-down panel (proves `fetch("data/bigrams.json")` resolves correctly from `/five/`).
- Clicking a trigram cell shows the completion list.
- Dark/light mode toggle works.
- Instant navigation works between `/`, `/five/`, `/ten/`.

**Commit:**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: bump zensical to >=0.0.33"
```
<!-- END_TASK_5 -->

<!-- START_TASK_6 -->
### Task 6: Final Phase 1 verification (full clean build)

**No file changes — verification only.**

**Implementation:**

Run a clean end-to-end build:

```bash
uv run python main.py
uv run zensical build --clean
```

Inspect `site/`:

```bash
find site -type f -name "index.html" | sort
```

Expected:
```
site/404.html
site/index.html
site/five/index.html
site/ten/index.html
```

Confirm absent:
```bash
find site -path '*dev_docs*' -o -path '*design-plans*' -o -path '*architecture*' -o -path '*implementation-plans*'
```

Expected: no output.

Confirm `data/` invariants for the design plan:

```bash
wc -l data/words.txt data/words_10.txt data/words_3_to_10.txt
awk 'length($0)!=5 || $0!~/^[a-z]+$/' data/words.txt | head
awk 'length($0)!=10 || $0!~/^[a-z]+$/' data/words_10.txt | head
awk 'length($0)<3 || length($0)>10 || $0!~/^[a-z]+$/' data/words_3_to_10.txt | head
```

Expected: line counts plausible (15,921 for words.txt; ~30k for words_10.txt; ~250k for words_3_to_10.txt). All three `awk` invocations produce no output (no malformed lines).

Run existing tests:

```bash
uv run pytest -q
```

Expected: all existing tests pass.

**No commit** for verification-only task.
<!-- END_TASK_6 -->
