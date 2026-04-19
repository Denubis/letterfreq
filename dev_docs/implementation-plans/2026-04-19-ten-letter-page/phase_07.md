# Ten-Letter Page Implementation Plan — Phase 7: Documentation update and freshness

**Goal:** Bring `CLAUDE.md` and `dependency-rationale.md` up to date for the new layout (`docs/five/`, `docs/ten/`, `letterfreq/` package, new corpus files, new entry script). Add `tests/test_corpora.py` to enforce the AC8 corpus-file invariants (`words_*.txt` shape) so accidental modification or regeneration drift is caught by CI.

**Architecture:** Documentation-only updates plus one new test file. No code or config changes beyond what was committed in Phases 1–6.

**Tech Stack:** No new tools.

**Scope:** Phase 7 of 7 from `/home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md`.

**Codebase verified:** 2026-04-19. CLAUDE.md was last updated 2026-04-19 (the dev_docs/ bootstrap commit) — that update added the dev_docs/ entries but kept the project-structure block describing only the *current* (pre-implementation) layout. After Phases 1–6 are done, `letterfreq/`, `main_ten.py`, `data/words_10.txt`, `data/words_3_to_10.txt`, `docs/five/`, `docs/ten/` all exist on disk and need to be reflected in CLAUDE.md.

**Phase Type:** infrastructure + functionality (one new test file for corpus invariants).

---

## Acceptance Criteria Coverage

This phase implements and tests:

### ten-letter-page.AC8: Corpus file invariants
- **ten-letter-page.AC8.1 Success:** `data/words_10.txt` is non-empty; every line matches `^[a-z]{10}$`.
- **ten-letter-page.AC8.2 Success:** `data/words_3_to_10.txt` is non-empty; every line matches `^[a-z]{3,10}$`.
- **ten-letter-page.AC8.3 Success (invariant):** `data/words.txt` (existing 5-letter) is non-empty, line count is at least 15,000, every line matches `^[a-z]{5}$`. Catches accidental modification by this refactor while remaining robust to legitimate future regeneration.

### ten-letter-page.AC9: Documentation freshness
- **ten-letter-page.AC9.1 Success:** `CLAUDE.md` references `docs/five/`, `docs/ten/`, `letterfreq/` package, `words_10.txt`, `words_3_to_10.txt`.
- **ten-letter-page.AC9.2 Success:** `CLAUDE.md` freshness date is `2026-04-19` or later.

---

## Implementation Tasks

<!-- START_TASK_1 -->
### Task 1: Add `tests/test_corpora.py` for AC8 invariants

**Verifies:** ten-letter-page.AC8.1, AC8.2, AC8.3.

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_corpora.py`

**Implementation:**

```python
"""Structural invariants for committed corpus files.

Catches accidental modification, malformed regeneration, or upstream
schema drift. Each invariant is a regex shape + a non-emptiness check;
no specific count or hash is pinned, so legitimate regeneration is OK.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "data"
WORDS_FILE = DATA_DIR / "words.txt"
WORDS_10_FILE = DATA_DIR / "words_10.txt"
WORDS_3_TO_10_FILE = DATA_DIR / "words_3_to_10.txt"

ALPHA_5 = re.compile(r"^[a-z]{5}$")
ALPHA_10 = re.compile(r"^[a-z]{10}$")
ALPHA_3_TO_10 = re.compile(r"^[a-z]{3,10}$")


def _read_lines(path: Path) -> list[str]:
    return [w for w in path.read_text().splitlines() if w]


# ---- AC8.3: existing 5-letter corpus ------------------------------------------

def test_words_txt_exists_and_nonempty() -> None:
    assert WORDS_FILE.exists(), f"{WORDS_FILE} missing"
    assert WORDS_FILE.stat().st_size > 0


def test_words_txt_minimum_count() -> None:
    """At least 15,000 entries — guards against accidental truncation."""
    lines = _read_lines(WORDS_FILE)
    assert len(lines) >= 15_000, f"expected >=15000 lines, got {len(lines)}"


def test_words_txt_all_lines_are_5_letter_lowercase_alpha() -> None:
    lines = _read_lines(WORDS_FILE)
    bad = [(i, line) for i, line in enumerate(lines, start=1)
           if not ALPHA_5.fullmatch(line)]
    assert not bad, f"non-conforming lines (line:value): {bad[:5]}"


# ---- AC8.1: 10-letter corpus --------------------------------------------------

def test_words_10_txt_exists_and_nonempty() -> None:
    assert WORDS_10_FILE.exists(), f"{WORDS_10_FILE} missing"
    assert WORDS_10_FILE.stat().st_size > 0


def test_words_10_txt_all_lines_are_10_letter_lowercase_alpha() -> None:
    lines = _read_lines(WORDS_10_FILE)
    assert lines, "words_10.txt is empty"
    bad = [(i, line) for i, line in enumerate(lines, start=1)
           if not ALPHA_10.fullmatch(line)]
    assert not bad, f"non-conforming lines (line:value): {bad[:5]}"


def test_words_10_txt_minimum_count() -> None:
    """Guards against an upstream regression that quietly produces a sparse corpus."""
    lines = _read_lines(WORDS_10_FILE)
    assert len(lines) >= 20_000, f"expected >=20000 ten-letter words, got {len(lines)}"


# ---- AC8.2: 3-10 letter baseline corpus ---------------------------------------

def test_words_3_to_10_txt_exists_and_nonempty() -> None:
    assert WORDS_3_TO_10_FILE.exists(), f"{WORDS_3_TO_10_FILE} missing"
    assert WORDS_3_TO_10_FILE.stat().st_size > 0


def test_words_3_to_10_txt_all_lines_are_3_to_10_letter_lowercase_alpha() -> None:
    lines = _read_lines(WORDS_3_TO_10_FILE)
    assert lines, "words_3_to_10.txt is empty"
    bad = [(i, line) for i, line in enumerate(lines, start=1)
           if not ALPHA_3_TO_10.fullmatch(line)]
    assert not bad, f"non-conforming lines (line:value): {bad[:5]}"


def test_words_3_to_10_txt_includes_all_lengths() -> None:
    """Sanity check: at least one word of each length 3..10 should be present."""
    lines = _read_lines(WORDS_3_TO_10_FILE)
    lengths_present = {len(w) for w in lines}
    expected = set(range(3, 11))
    missing = expected - lengths_present
    assert not missing, f"baseline corpus missing word lengths: {sorted(missing)}"


def test_words_3_to_10_txt_minimum_count() -> None:
    """Guards against an upstream regression that quietly produces a sparse baseline."""
    lines = _read_lines(WORDS_3_TO_10_FILE)
    assert len(lines) >= 100_000, f"expected >=100000 baseline words, got {len(lines)}"
```

**Verification:**

```bash
uv run pytest tests/test_corpora.py -v
```

Expected: 10 tests pass.

Run the full suite:

```bash
uv run pytest -q
```

Expected: all tests across all files pass (test_frequencies, test_reference, test_scoring, test_render_reference, test_render_ranking, test_corpora).

**Commit:**

```bash
git add tests/test_corpora.py
git commit -m "test: add corpus-file structural invariants (AC8)"
```
<!-- END_TASK_1 -->

<!-- START_TASK_1B -->
### Task 1B: Add `tests/test_documentation.py` for AC9 (CLAUDE.md content + freshness)

**Verifies:** ten-letter-page.AC9.1, AC9.2.

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_documentation.py`

**Implementation:**

```python
"""Structural assertions for project documentation (AC9.1, AC9.2)."""

from __future__ import annotations

import re
from pathlib import Path

CLAUDE_MD = Path(__file__).parent.parent / "CLAUDE.md"


def _read() -> str:
    assert CLAUDE_MD.exists(), f"{CLAUDE_MD} missing"
    return CLAUDE_MD.read_text()


# AC9.1
def test_claude_md_references_new_layout() -> None:
    text = _read()
    expected_substrings = [
        "docs/five/",
        "docs/ten/",
        "letterfreq/",
        "words_10.txt",
        "words_3_to_10.txt",
    ]
    missing = [s for s in expected_substrings if s not in text]
    assert not missing, f"CLAUDE.md missing references: {missing}"


# AC9.2
def test_claude_md_freshness_date_is_recent_enough() -> None:
    text = _read()
    match = re.search(r"^Freshness:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.MULTILINE)
    assert match, "CLAUDE.md is missing a 'Freshness: YYYY-MM-DD' line"
    date_str = match.group(1)
    assert date_str >= "2026-04-19", (
        f"CLAUDE.md freshness date {date_str!r} is older than 2026-04-19; "
        "update the freshness line when CLAUDE.md content changes."
    )
```

**Verification:**

```bash
uv run pytest tests/test_documentation.py -v
```

Expected: 2 tests pass (assuming Phase 7 Task 2 has rewritten CLAUDE.md to mention all five paths and updated the freshness line).

**Commit:**

```bash
git add tests/test_documentation.py
git commit -m "test: add AC9 documentation invariants (CLAUDE.md content + freshness)"
```
<!-- END_TASK_1B -->


<!-- START_TASK_1C -->
### Task 1C: Add `tests/test_site_isolation.py` — defensive dev_docs-leak guard

**Verifies:** Closes the gap noted by peer review M3 — the dev_docs/ exclusion relies on Zensical's default `docs_dir = "docs"`. A future contributor adding `docs_dir = "."` (or some Zensical default change) would silently publish all of dev_docs/. A static check on zensical.toml + filesystem layout catches the obvious failure modes cheaply, without running a build.

**Files:**
- Create: `/home/brian/llm/letterfreq/tests/test_site_isolation.py`

**Implementation:**

```python
"""Defensive tests that dev_docs/ stays out of the published Zensical site."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ZENSICAL_TOML = REPO_ROOT / "zensical.toml"
DOCS_DIR = REPO_ROOT / "docs"
DEV_DOCS_DIR = REPO_ROOT / "dev_docs"


def test_dev_docs_lives_outside_docs() -> None:
    """dev_docs/ must be a sibling of docs/, NOT a subdirectory."""
    assert DEV_DOCS_DIR.is_dir(), "dev_docs/ missing at repo root"
    assert not (DOCS_DIR / "dev_docs").exists(), (
        "dev_docs/ leaked into docs/ — Zensical would publish it"
    )


def test_zensical_docs_dir_remains_default_or_explicitly_docs() -> None:
    """If docs_dir is set explicitly, it must be 'docs' (not '.' or anything broader)."""
    text = ZENSICAL_TOML.read_text()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"docs_dir\s*=\s*[\"']([^\"']+)[\"']", stripped)
        if match:
            value = match.group(1)
            assert value == "docs", (
                f"zensical.toml docs_dir = {value!r}; only 'docs' is safe — "
                "anything broader risks publishing dev_docs/"
            )


def test_no_meta_doc_directories_under_docs() -> None:
    """Sanity: design-plans/, architecture/, implementation-plans/ must not exist under docs/."""
    bad = []
    for name in ("design-plans", "architecture", "implementation-plans", "dev_docs"):
        if (DOCS_DIR / name).exists():
            bad.append(f"docs/{name}")
    assert not bad, f"meta-doc directories leaked into docs/: {bad}"
```

**Verification:**

```bash
uv run pytest tests/test_site_isolation.py -v
```

Expected: 3 tests pass.

**Commit:**

```bash
git add tests/test_site_isolation.py
git commit -m "test: defensive dev_docs/ vs docs/ isolation guards"
```
<!-- END_TASK_1C -->

<!-- START_TASK_2 -->
### Task 2: Refresh `CLAUDE.md` for the new layout

**Verifies:** ten-letter-page.AC9.1, AC9.2.

**Files:**
- Modify: `/home/brian/llm/letterfreq/CLAUDE.md` (Stack section, project-structure block, Architecture section, Freshness line).

**Implementation:**

Replace the entire `# letterfreq` document body to reflect the post-implementation state. The new content:

```markdown
# letterfreq

Letter, bigram, and trigram frequency analyses of English words from
[dwyl/english-words](https://github.com/dwyl/english-words), published as a
static site with two analyses: a five-letter positional analysis and a
ten-letter ranking analysis.

## Stack

- **Python 3.14** with **uv** for package management
- **Polars** for five-letter positional frequency computation in `main.py`
- **Plain dicts** (no DataFrame) for ten-letter computation in `letterfreq/` (simpler for the smaller, position-independent counts)
- **Zensical** (>=0.0.33) for static site generation — successor to mkdocs-material by squidfunk
- **GitHub Pages** for hosting via `.github/workflows/docs.yml`

## Project structure

```
docs/                           — Zensical source directory (everything here is published)
docs/index.md                   — Landing page (links to /five/ and /ten/)
docs/five/                      — Five-letter analysis page
docs/five/index.md              — Generated by main.py (do not edit by hand)
docs/five/data/                 — Runtime JSON (bigrams + trigrams loaded by JS)
docs/ten/                       — Ten-letter analysis page
docs/ten/index.md               — Generated by main_ten.py (do not edit by hand)
docs/js/sort-tables.js          — Sortable tables, per-column normalisation, bigram drill-downs
docs/js/trigram-expand.js       — Trigram click-to-expand completion lists
docs/css/heatmap.css            — Heatmap colour scales, frequency bars, drill-downs, .ref-pair layout
main.py                         — Generates docs/five/index.md (positional five-letter analysis)
main_ten.py                     — Generates docs/ten/index.md (ten-letter rankings + baseline references)
letterfreq/                     — Pure functional core for the ten-letter analysis
letterfreq/reference.py         — Baseline frequency counters (letter, bigram, start/end trigram, first/last)
letterfreq/scoring.py           — Per-word scoring (letter-coverage, bigram, trigram, positional endpoint)
letterfreq/render.py            — HTML renderers for reference and ranking tables
scripts/build_corpora.py        — One-shot helper that downloads dwyl/english-words and writes data/words_{10,3_to_10}.txt
data/words.txt                  — Five-letter corpus (committed; ~15,921 words)
data/words_10.txt               — Ten-letter corpus (committed)
data/words_3_to_10.txt          — Baseline corpus for ten-letter reference frequencies (committed)
dependency-rationale.md         — Falsifiable justifications for every direct dependency (repo root, not in docs/)
tests/                          — Pytest suite: frequency, scoring, rendering, corpus invariants
zensical.toml                   — Zensical configuration (TOML, not mkdocs.yml)
site/                           — Build output (gitignored)
dev_docs/                       — Project meta-docs NOT published by Zensical (kept outside docs/ on purpose; Zensical 0.0.33 has no exclude_docs/not_in_nav support)
dev_docs/design-plans/          — Validated design plans (e.g. ten-letter page)
dev_docs/architecture/          — Architecture reference: glossary.md, personae.md, constraints.md, dfd/
dev_docs/implementation-plans/  — Detailed task-level plans generated from design plans
```

## Commands

```bash
uv run python main.py           # Regenerate /five/ frequency data + page content
uv run python main_ten.py       # Regenerate /ten/ ranking + reference data + page content
uv run zensical serve           # Local preview at http://localhost:8000
uv run zensical build --clean   # Build static site to site/
uv run pytest                   # Run all tests
uv run python scripts/build_corpora.py  # Re-fetch and rebuild data/words_{10,3_to_10}.txt from upstream
```

## Architecture

Static-first design. Two entry scripts produce two pages:

**`/five/` (main.py — Polars-backed positional analysis):**
- **Overall frequency:** Static sorted table (sortable via JS)
- **Unigrams:** Static 26×5 heatmap (coloured cells)
- **Bigrams:** 4 heading-structured 26×26 grids; clicking any cell or header shows neighbour-frequency drill-down bars via JS loading `docs/five/data/bigrams.json`
- **Trigrams:** 9 static 26×26 grids (3 gap positions × 3 word windows); clicking a cell shows completion lists via JS loading `docs/five/data/trigrams.json`

**`/ten/` (main_ten.py + letterfreq/ — position-independent ranking analysis):**
- **Reference tables (computed over 3–10 letter baseline):** letter frequency (26 rows), top-100 bigram frequency, side-by-side start/end trigram pair (top-50 each), side-by-side first-letter/last-letter pair (26 rows each).
- **Ranking tables (over 10-letter words):** four top-50 tables ranked by letter-coverage score (Σ over distinct letters), bigram score (Σ over 9 consecutive bigrams), start+end trigram score, and positional first+last score (no distinct cap on endpoints — both contribute even if w[0] == w[-1], per DR8 in the design plan).

Two JS files (shared across pages): `sort-tables.js` (table sorting, per-column normalisation, bigram drill-downs) and `trigram-expand.js` (trigram completion lists). Both use event delegation and bare-relative `fetch("data/<file>.json")`, which resolves correctly because the JSON data is co-located with each page.

The `letterfreq/` package follows FCIS: pure functions in `reference.py`, `scoring.py`, `render.py`; orchestration and I/O in `main_ten.py`. `main.py` (the older five-letter pipeline) was not refactored into the package — the package is for the new ten-letter analysis only.

Freshness: 2026-04-19
```

**Verification:**

```bash
grep -n 'docs/ten\|docs/five\|letterfreq/\|words_10\|words_3_to_10' CLAUDE.md
```

Expected: at least one match for each of the 5 grep terms.

```bash
grep -n 'Freshness:' CLAUDE.md
```

Expected: `Freshness: 2026-04-19` (or later).

**Commit:**

```bash
git add CLAUDE.md
git commit -m "docs: refresh CLAUDE.md for /ten/ page, letterfreq/ package, new corpora"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Verify `dependency-rationale.md` is current

**Verifies:** No-new-deps invariant from the design plan's "Done when" for Phase 7 (`dependency-rationale.md` (repo root) is current).

**Files:**
- (Possibly) Modify: `/home/brian/llm/letterfreq/dependency-rationale.md` (only if a real change is needed).

**Implementation:**

Read the current `dependency-rationale.md`:

```bash
cat dependency-rationale.md
```

Confirm three entries exist (polars, zensical, pytest). The Zensical version bump (0.0.28 → 0.0.33) does NOT require a new entry — the dependency itself is unchanged, only the version pin moved.

If the existing `zensical` entry's evidence line still references only `docs/index.md`, optionally update the evidence line to mention `docs/five/index.md` and `docs/ten/index.md`. This is a low-stakes refresh — skip if the existing evidence is still defensible (it cites `zensical.toml` and the workflow, which are sufficient).

If you make any change, commit:

```bash
git add dependency-rationale.md
git commit -m "docs: refresh zensical entry evidence in dependency-rationale.md"
```

If no change is needed, no commit.

**Verification:**

```bash
grep -E '^## (polars|zensical|pytest)' dependency-rationale.md
```

Expected: three matches (one per entry header).

```bash
grep -i 'zensical>=0' pyproject.toml
```

Expected: `zensical>=0.0.33` (already bumped in Phase 1's Task 5).
<!-- END_TASK_3 -->

<!-- START_TASK_4 -->
### Task 4: Final sweep — full test run and clean build

**No file changes — verification only.**

**Implementation:**

```bash
uv run pytest -q
uv run python main.py
uv run python main_ten.py
uv run zensical build --clean
```

Expected:
- pytest: all tests pass (test_frequencies, test_reference, test_scoring, test_render_reference, test_render_ranking, test_corpora).
- main.py: prints generated /five/ index.
- main_ten.py: prints generated /ten/ index.
- zensical build: succeeds.

Confirm the published site has all expected pages and no dev-doc leakage:

```bash
find site -name 'index.html' -type f | sort
find site \( -path '*dev_docs*' -o -path '*design-plans*' -o -path '*architecture*' -o -path '*implementation-plans*' \) -print
```

Expected: `site/index.html`, `site/five/index.html`, `site/ten/index.html` exist; second find returns nothing.

**No commit** — the verification establishes that all 7 phases have landed correctly.
<!-- END_TASK_4 -->
