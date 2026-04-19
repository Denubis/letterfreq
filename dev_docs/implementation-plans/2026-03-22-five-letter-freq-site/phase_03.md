# Five-Letter Word Frequency Site — Phase 3: Bigram Grids

**Goal:** Add 4 collapsible 26×26 bigram heatmap grids (positions 1-2, 2-3, 3-4, 4-5) to the page.

**Architecture:** Extend `main.py` to compute 4 bigram matrices (pairs of adjacent positions), then generate 26×26 HTML heatmap tables wrapped in `<details>` elements for collapsibility. Reuse the colour scale approach from Phase 2. Each grid is independently normalised.

**Tech Stack:** Python 3.14, Polars

**Scope:** Phase 3 of 5 from original design

**Codebase verified:** 2026-03-23 (Phase 2 establishes heatmap generation patterns and CSS)

---

## Acceptance Criteria Coverage

This phase implements and tests:

### five-letter-freq-site.AC2: Frequency data is correct
- **five-letter-freq-site.AC2.3 Success:** Bigram counts for positions 1-2 sum to word_count

---

<!-- START_SUBCOMPONENT_A (tasks 1-3) -->
<!-- START_TASK_1 -->
### Task 1: Implement bigram computation in main.py

**Files:**
- Modify: `main.py` (add bigram computation function)

**Implementation:**

Add a function that:
1. Takes the words DataFrame
2. For each adjacent position pair (1-2, 2-3, 3-4, 4-5), extracts the two letters
3. Groups by the pair to count co-occurrences
4. Returns a dict keyed by pair name (e.g. `"1_2"`) with values being a nested dict: `{first_letter: {second_letter: count}}`

Polars approach:
- For each pair (i, i+1): extract `pl.col("word").str.slice(i, 1)` and `pl.col("word").str.slice(i+1, 1)`
- Group by both columns and count
- Pivot or convert to nested dict

Ensure zero-count pairs are omitted from the dict (sparse representation).

**Verification:**

```bash
uv run python main.py
```

Expected: `main.py` runs without error. Bigram data is computed (verified in Task 3 by tests).

**Commit:**

```bash
git add main.py
git commit -m "feat: add bigram frequency computation for adjacent positions"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Generate collapsible bigram heatmap HTML

**Files:**
- Modify: `main.py` (add bigram HTML generation to page output)
- Modify: `docs/css/heatmap.css` (add styles for collapsible sections and 26×26 grids)

**Implementation:**

Extend page generation to add a `## Positional Bigrams` section. For each of the 4 position pairs, generate:

```html
<details>
<summary>Positions X–Y</summary>
<table class="heatmap bigram-grid">
  <tr><th></th><th>a</th><th>b</th>...<th>z</th></tr>
  <tr><th>a</th><td style="background-color:...">N</td>...</tr>
  ...
</table>
</details>
```

- Row = letter at earlier position, Column = letter at later position
- Cell colour: same interpolation as unigrams, but normalised per-grid (each grid has its own max)
- Empty cells (0 count): leave white/no background, display nothing or "0"
- Use Zensical-compatible HTML within Markdown (raw HTML blocks)

Add to `docs/css/heatmap.css`:
- `.bigram-grid` — smaller font size for 26×26, compact cell sizing
- `.bigram-grid td` — min-width smaller than unigram cells
- `details summary` — cursor pointer, padding

**Verification:**

```bash
uv run python main.py && uv run zensical build --clean
```

Expected: Site builds. 4 collapsible bigram sections appear. Expanding one shows a 26×26 coloured grid.

**Commit:**

```bash
git add main.py docs/css/heatmap.css
git commit -m "feat: generate collapsible bigram heatmap grids"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Write tests for bigram count correctness

**Verifies:** five-letter-freq-site.AC2.3

**Files:**
- Modify: `tests/test_frequencies.py` (add bigram tests)

**Testing:**

Tests must verify:
- five-letter-freq-site.AC2.3: For the positions 1-2 bigram grid, the sum of all cell counts equals word_count (each word contributes exactly one bigram at positions 1-2)

Approach:
- Call the bigram computation function
- For the "1_2" pair: sum all counts across the nested dict
- Assert total == word_count
- Repeat for at least one other pair (e.g. "4_5") as a sanity check
- Spot-check: count words matching `^th...` to verify the (t, h) cell in the 1-2 grid

**Verification:**

```bash
uv run pytest tests/test_frequencies.py -v
```

Expected: All tests pass.

**Commit:**

```bash
git add tests/test_frequencies.py
git commit -m "test: add bigram count validation"
```
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->
