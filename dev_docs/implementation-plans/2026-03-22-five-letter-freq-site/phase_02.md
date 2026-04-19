# Five-Letter Word Frequency Site — Phase 2: Positional Unigram Heatmap

**Goal:** Add a 26×5 positional unigram heatmap as a static HTML table with coloured cells to the generated page.

**Architecture:** Extend `main.py` to compute per-position letter counts using Polars `group_by(["letter", "position"])`, then generate a 26-row × 5-column HTML table with inline `background-color` styles derived from a white-to-colour gradient based on relative frequency.

**Tech Stack:** Python 3.14, Polars

**Scope:** Phase 2 of 5 from original design

**Codebase verified:** 2026-03-23 (Phase 1 establishes main.py, page generation, CSS, tests)

---

## Acceptance Criteria Coverage

This phase implements and tests:

### five-letter-freq-site.AC2: Frequency data is correct
- **five-letter-freq-site.AC2.2 Success:** Unigram positional counts per position sum to word_count

---

<!-- START_SUBCOMPONENT_A (tasks 1-3) -->
<!-- START_TASK_1 -->
### Task 1: Implement positional unigram computation in main.py

**Files:**
- Modify: `main.py` (add unigram computation function)

**Implementation:**

Add a function to `main.py` that:
1. Takes the DataFrame of words (already loaded in Phase 1)
2. For each word, extracts each letter with its position (1-5)
3. Creates a long-format DataFrame with columns: `letter`, `position`
4. Groups by `["letter", "position"]` and counts
5. Returns a dict structure: `{letter: [pos1_count, pos2_count, pos3_count, pos4_count, pos5_count]}` for all 26 letters

Polars approach:
- Start from the words DataFrame
- Use `.with_columns()` to extract each position: `pl.col("word").str.slice(i, 1).alias(f"pos{i+1}")` for i in 0..4
- `.unpivot()` (formerly `.melt()`) to go from wide to long format
- `.group_by(["value", "variable"]).len()` to count
- `.pivot()` to get letter × position matrix

**Verification:**

```bash
uv run python main.py
```

Expected: `main.py` runs without error. Unigram data is computed (verified in Task 3 by tests).

**Commit:**

```bash
git add main.py
git commit -m "feat: add positional unigram frequency computation"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Generate unigram heatmap HTML and update CSS

**Files:**
- Modify: `main.py` (add heatmap HTML generation to page output)
- Modify: `docs/css/heatmap.css` (add heatmap cell styles)

**Implementation:**

Extend the page generation in `main.py` to add a `## Positional Unigrams` section after the overall frequency table. Generate a `<table class="heatmap">` with:
- Header row: empty cell + "Pos 1" through "Pos 5"
- 26 data rows (a-z): letter label + 5 cells
- Each cell contains the raw count
- Each cell has `style="background-color: rgb(R, G, B)"` where the colour is interpolated from white (0 count) to a saturated colour (max count in the grid)

Colour interpolation: for each cell, compute `intensity = count / max_count_in_grid`. Then `rgb = (255, 255 - round(intensity * 200), 255 - round(intensity * 200))` for a white-to-red scale (or similar). The exact colour scheme can be adjusted.

Add to `docs/css/heatmap.css`:
- `.heatmap` — table layout, fixed cell widths for uniform grid
- `.heatmap td` — text alignment center, min-width, padding
- `.heatmap th` — header styling
- `.heatmap .row-label` — letter labels styling

**Verification:**

```bash
uv run python main.py && uv run zensical build --clean
```

Expected: Site builds. Open `site/index.html` — the unigram heatmap appears with coloured cells.

**Commit:**

```bash
git add main.py docs/css/heatmap.css
git commit -m "feat: generate positional unigram heatmap with colour scale"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Write tests for unigram positional counts

**Verifies:** five-letter-freq-site.AC2.2

**Files:**
- Modify: `tests/test_frequencies.py` (add unigram tests)

**Testing:**

Tests must verify:
- five-letter-freq-site.AC2.2: For each position (1-5), the sum of all 26 letter counts at that position equals word_count

Approach:
- Call the unigram computation function from `main.py`
- For each position column, assert `sum(counts_at_position) == word_count`
- Verify all 26 letters have entries (even if count is 0)
- Spot-check: manually verify a known value (e.g. count of 'e' at position 5 using `grep -c '^[a-z]\{4\}e$' /usr/share/dict/words`)

**Verification:**

```bash
uv run pytest tests/test_frequencies.py -v
```

Expected: All tests pass, including new unigram tests.

**Commit:**

```bash
git add tests/test_frequencies.py
git commit -m "test: add positional unigram count validation"
```
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->
