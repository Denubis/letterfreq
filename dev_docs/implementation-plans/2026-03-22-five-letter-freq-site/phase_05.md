# Five-Letter Word Frequency Site — Phase 5: Trigram Grids with JS Click-to-Expand

**Goal:** Add 9 trigram heatmap grids (3 gap positions × 3 word windows) with JavaScript-driven click-to-expand completion lists.

**Architecture:** Extend `main.py` to compute trigram gap data, write `docs/data/trigrams.json`, and generate 9 static 26×26 HTML grids with `data-*` attributes for JS binding. A small JS script (`docs/js/trigram-expand.js`) loads the JSON on first click and populates a completion list `<div>` below the clicked cell. Trigram grids are organised under headings by gap position, with sub-headings for word windows.

**Tech Stack:** Python 3.14, Polars, vanilla JavaScript

**Scope:** Phase 5 of 5 from original design

**Codebase verified:** 2026-03-23 (Phase 4 establishes all static HTML patterns)

---

## Acceptance Criteria Coverage

This phase implements and tests:

### five-letter-freq-site.AC4: Trigram click-to-expand
- **five-letter-freq-site.AC4.1 Success:** Clicking a non-empty trigram cell shows sorted completion list with counts and percentages
- **five-letter-freq-site.AC4.2 Edge:** Clicking an empty cell shows "No completions" or similar (no error)

### five-letter-freq-site.AC2: Frequency data is correct
- **five-letter-freq-site.AC2.4 Success:** Trigram gap completions for a known pair match manual grep verification

---

<!-- START_SUBCOMPONENT_A (tasks 1-3) -->
<!-- START_TASK_1 -->
### Task 1: Implement trigram gap computation and write JSON

**Files:**
- Modify: `main.py` (add trigram computation, write JSON)

**Implementation:**

Add a function that computes trigram gap frequencies:

For each of 3 gap positions (1st, 2nd, 3rd letter in the trigram) × 3 word windows (positions 1-2-3, 2-3-4, 3-4-5):
1. Extract the three letters at the window positions
2. The "gap" position is the unknown; the other two are "known"
3. Group by (known_letter_1, known_letter_2, gap_letter) and count
4. Structure as nested dict: `known1 → known2 → {gap_letter: count}`

Key naming: `gap1_win123` means gap at position 1 of the trigram (i.e. the first letter in the window is unknown), word window is positions 1-2-3.

For `gap1_win123`: known letters are at word positions 2 and 3, gap letter is at word position 1.
For `gap2_win123`: known letters are at word positions 1 and 3, gap letter is at word position 2.
For `gap3_win123`: known letters are at word positions 1 and 2, gap letter is at word position 3.

**Axis ordering convention:** For each combination, `known1` is always the lower-indexed word position and `known2` is the higher-indexed word position. In the JSON structure, the outer key is `known1` and the inner key is `known2`. In the HTML grid, rows correspond to `known1` and columns to `known2`. This convention must be consistent across the JSON writer (this task), the HTML generator (Task 2), and the JS consumer (Task 3).

Similarly for `win234` and `win345`.

Write the complete structure to `docs/data/trigrams.json`. Omit zero-count entries (sparse representation).

Also compute a summary matrix for each of the 9 combinations: for each (known1, known2) pair, the total count across all gap letters. This is used for heatmap colouring.

**Verification:**

```bash
uv run python main.py
cat docs/data/trigrams.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d), 'keys')"
```

Expected: 9 keys in the JSON.

**Commit:**

```bash
git add main.py docs/data/trigrams.json
git commit -m "feat: compute trigram gap frequencies and write JSON"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Generate trigram grid HTML with data attributes

**Files:**
- Modify: `main.py` (add trigram HTML generation to page output)
- Modify: `docs/css/heatmap.css` (add trigram grid and completion list styles)

**Implementation:**

Extend page generation to add a `## Positional Trigrams` section. Structure:

```markdown
## Positional Trigrams

### Gap at position 1 (_XY)

#### Word positions 1-2-3

<table class="heatmap trigram-grid" data-grid="gap1_win123">
  <tr><th></th><th>a</th>...<th>z</th></tr>
  <tr>
    <th>a</th>
    <td class="trigram-cell" data-known1="a" data-known2="a" data-count="5"
        style="background-color:...">5</td>
    ...
  </tr>
</table>
<div class="trigram-expansion" id="expand-gap1_win123"></div>

#### Word positions 2-3-4
...

### Gap at position 2 (X_Y)
...

### Gap at position 3 (XY_)
...
```

Each cell has:
- `data-known1`, `data-known2`: the two known letters
- `data-count`: total count for that pair (used for display)
- `data-grid`: which trigram combination this cell belongs to (on the table)
- Inline `background-color` based on count relative to grid max
- CSS class `trigram-cell` for JS binding

Empty cells (count 0): no data attributes, no background colour, empty content. Add class `empty`.

Below each grid, a `<div class="trigram-expansion">` placeholder for JS to populate.

Add to `docs/css/heatmap.css`:
- `.trigram-grid` — same compact sizing as bigram grids
- `.trigram-cell` — cursor pointer on non-empty cells
- `.trigram-cell.empty` — cursor default, muted appearance
- `.trigram-expansion` — container for completion list, hidden by default
- `.completion-list` — sorted list styling
- `.completion-item` — individual completion entry with bar

**Verification:**

```bash
uv run python main.py && uv run zensical build --clean
```

Expected: Site builds. 9 trigram grids appear under appropriate headings. Cells are coloured. Clicking does nothing yet (JS not loaded).

**Commit:**

```bash
git add main.py docs/css/heatmap.css
git commit -m "feat: generate trigram heatmap grids with data attributes"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Implement trigram-expand.js

**Files:**
- Create: `docs/js/trigram-expand.js`
- Modify: `zensical.toml` (add extra_javascript)

**Implementation:**

Create `docs/js/trigram-expand.js` with this behaviour:

1. On DOMContentLoaded, add click event listeners to all `.trigram-cell:not(.empty)` elements
2. On first click of any trigram cell: fetch `data/trigrams.json` (relative URL), parse, cache in a variable
3. On click of a specific cell:
   - Read `data-grid`, `data-known1`, `data-known2` from the cell
   - Look up the completion data: `trigramData[grid][known1][known2]`
   - Sort completions by descending count
   - Compute total for percentages
   - Build HTML: a `<div class="completion-list">` with items showing letter, count, percentage bar
   - Find the grid's `<div class="trigram-expansion">` sibling and set its innerHTML
   - Show the expansion div
4. Clicking the same cell again hides the expansion
5. Clicking a different cell replaces the expansion content
6. Clicking an empty cell: no-op (no event listener attached)

If `trigramData[grid][known1][known2]` is undefined (pair has no completions but somehow the cell was non-empty), show "No completions found."

Update `zensical.toml` to add:
```toml
extra_javascript = ["js/trigram-expand.js"]
```

**Verification:**

```bash
uv run python main.py && uv run zensical serve
```

Expected: Open `http://localhost:8000`, navigate to trigram section. Click a coloured cell — a completion list appears below the grid. Click an empty area — nothing happens. Click another cell — list updates.

**Commit:**

```bash
git add docs/js/trigram-expand.js zensical.toml
git commit -m "feat: add trigram click-to-expand JS and configure Zensical"
```
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->

<!-- START_TASK_4 -->
### Task 4: Write tests for trigram data correctness

**Verifies:** five-letter-freq-site.AC2.4, five-letter-freq-site.AC4.1, five-letter-freq-site.AC4.2

**Files:**
- Modify: `tests/test_frequencies.py` (add trigram tests)

**Testing:**

Tests must verify:
- five-letter-freq-site.AC2.4: For a known pair of letters at specific positions, the gap completions match a manual grep count. Example: for gap1_win123 with known2='h' and known3='e', count how many lowercase 5-letter words match `^.he..` and verify the gap completions sum to that count.
- five-letter-freq-site.AC4.1: The trigram data structure has the expected shape — 9 top-level keys, nested dicts for non-empty pairs
- five-letter-freq-site.AC4.2: Looking up a pair that has no words returns None/missing key (the JS handles this as "No completions")

Approach:
- Load the computed trigram data (call the computation function)
- Verify 9 keys exist
- Pick a known pair and verify counts against `grep -c` on the word list
- Verify a known-empty pair returns no data

**Verification:**

```bash
uv run pytest tests/test_frequencies.py -v
```

Expected: All tests pass.

**Commit:**

```bash
git add tests/test_frequencies.py
git commit -m "test: add trigram data correctness validation"
```
<!-- END_TASK_4 -->
