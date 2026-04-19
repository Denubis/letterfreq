# Five-Letter Word Frequency Site — Phase 4: Bigram Row Drill-Downs

**Goal:** Add click-to-expand drill-downs on bigram row headers showing ±1 neighbour frequency distributions for that letter at that position.

**Architecture:** Extend the bigram grid HTML generation to nest `<details>` elements inside each row. When a row header (letter label) is clicked, it expands to show frequency bars for the letters that appear at the adjacent positions (one before, one after). Edge positions (1, 5) get only one neighbour bar. This uses the bigram data already computed in Phase 3 — no new computation needed, just different slicing of the same data.

**Tech Stack:** Python 3.14, Polars

**Scope:** Phase 4 of 5 from original design

**Codebase verified:** 2026-03-23 (Phase 3 establishes bigram grids and collapsible patterns)

---

## Acceptance Criteria Coverage

This phase implements and tests:

### five-letter-freq-site.AC3: Bigram drill-down
- **five-letter-freq-site.AC3.1 Success:** Clicking a bigram row header expands to show neighbour frequency bars for that letter at that position
- **five-letter-freq-site.AC3.2 Success:** Edge positions (1, 5) show only one neighbour; middle positions show two
- **five-letter-freq-site.AC3.3 Edge:** Row header for a letter with zero occurrences at that position shows empty or absent drill-down

---

<!-- START_TASK_1 -->
### Task 1: Implement neighbour frequency computation

**Files:**
- Modify: `main.py` (add neighbour distribution function)

**Implementation:**

Add a function that, given a letter and a position (1-5), returns the frequency distributions of letters at adjacent positions where the given letter appears:

For letter 'T' at position 2 in the positions 1-2 grid:
- **Left neighbour (position 1):** From the 1-2 bigram data, filter where position-2 letter == 'T', return position-1 letter counts. This is the column slice for 'T' in the 1-2 grid.
- **Right neighbour (position 3):** From the 2-3 bigram data, filter where position-2 letter == 'T', return position-3 letter counts. This is the row slice for 'T' in the 2-3 grid.

For position 1: only right neighbour (from 1-2 grid, row slice for the letter).
For position 5: only left neighbour (from 4-5 grid, column slice for the letter).
For positions 2-4: both neighbours available.

This function reuses bigram data from Phase 3 — it's just a different view into the same matrices.

**Verification:**

```bash
uv run python main.py
```

Expected: `main.py` runs without error. Neighbour distributions are computed (verified in Task 3 by tests).

**Commit:**

```bash
git add main.py
git commit -m "feat: add neighbour frequency distribution computation"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Generate drill-down HTML inside bigram grids

**Files:**
- Modify: `main.py` (extend bigram HTML generation with nested details)
- Modify: `docs/css/heatmap.css` (add drill-down bar styles)

**Implementation:**

Modify the bigram grid HTML generation from Phase 3. For each row in each bigram grid, replace the plain `<th>` row header with a `<details>` element:

```html
<tr>
  <th>
    <details class="drill-down">
      <summary>t</summary>
      <div class="neighbour-bars">
        <h4>Position 1 → t</h4>
        <div class="bar-row"><span class="bar-label">s</span><span class="bar" style="width: 45%"></span><span class="bar-count">234</span></div>
        <div class="bar-row"><span class="bar-label">a</span><span class="bar" style="width: 30%"></span><span class="bar-count">156</span></div>
        ...
        <h4>t → Position 3</h4>
        <div class="bar-row">...</div>
      </div>
    </details>
  </th>
  <td>...</td>
  ...
</tr>
```

For each letter at each position:
- If the letter has zero total occurrences at that position (sum of row is 0), omit the drill-down — just show the letter as plain text
- For edge positions (position 1 in 1-2 grid): show only "→ Position 2" bars
- For edge positions (position 5 in 4-5 grid): show only "Position 4 →" bars
- For the earlier position in each grid (e.g. position 2 in 2-3 grid): show both neighbours

Bars are sorted by descending count. Only show letters with count > 0.
Bar width: percentage of max count in that distribution.

Add to `docs/css/heatmap.css`:
- `.drill-down` — inline display within table header
- `.drill-down summary` — cursor pointer, display matches letter labels
- `.neighbour-bars` — layout for the bar chart
- `.bar-row` — flex row with label, bar, count
- `.bar` — coloured bar with transition

**Verification:**

```bash
uv run python main.py && uv run zensical build --clean
```

Expected: Site builds. In a bigram grid, clicking a row letter expands to show neighbour frequency bars. Position 1 shows only right neighbour. Position 5 shows only left.

**Commit:**

```bash
git add main.py docs/css/heatmap.css
git commit -m "feat: add bigram row drill-downs with neighbour frequency bars"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Write tests for drill-down correctness

**Verifies:** five-letter-freq-site.AC3.1, five-letter-freq-site.AC3.2, five-letter-freq-site.AC3.3

**Files:**
- Modify: `tests/test_frequencies.py` (add drill-down tests)

**Testing:**

Tests must verify:
- five-letter-freq-site.AC3.1: For a known letter (e.g. 'T' at position 2), the neighbour distribution counts match the expected values from the bigram data
- five-letter-freq-site.AC3.2: For position 1, the function returns only a right neighbour; for position 5, only a left neighbour; for position 3, both
- five-letter-freq-site.AC3.3: For a letter that never appears at a given position (find one empirically, or use a synthetic test), the function returns empty distributions

Approach:
- Test the neighbour computation function directly
- Verify structure (number of neighbour directions returned) matches position rules
- Cross-check: the sum of neighbour counts for letter X at position N should equal the total occurrences of X at position N (from unigram data)

**Verification:**

```bash
uv run pytest tests/test_frequencies.py -v
```

Expected: All tests pass.

**Commit:**

```bash
git add tests/test_frequencies.py
git commit -m "test: add bigram drill-down validation"
```
<!-- END_TASK_3 -->
