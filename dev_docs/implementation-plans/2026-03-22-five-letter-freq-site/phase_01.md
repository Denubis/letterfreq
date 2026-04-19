# Five-Letter Word Frequency Site — Phase 1: Data Pipeline and Deployment Smoke Test

**Goal:** Compute overall letter frequencies from the word list, generate the page, and verify the full build-deploy pipeline works end-to-end.

**Architecture:** Python script reads `/usr/share/dict/words`, filters to lowercase 5-letter words, computes overall letter frequencies with Polars, generates `docs/index.md` with a static HTML frequency table. Zensical builds the site. GitHub Actions deploys to Pages.

**Tech Stack:** Python 3.14, Polars, Zensical, uv, GitHub Actions

**Scope:** Phase 1 of 5 from original design

**Codebase verified:** 2026-03-23

---

## Acceptance Criteria Coverage

This phase implements and tests:

### five-letter-freq-site.AC1: Site builds and deploys
- **five-letter-freq-site.AC1.1 Success:** `uv run zensical build --clean` exits 0 and produces `site/` directory

### five-letter-freq-site.AC2: Frequency data is correct
- **five-letter-freq-site.AC2.1 Success:** Overall frequencies sum to 5 x word_count (every word contributes 5 letters)

### five-letter-freq-site.AC5: No external runtime dependencies
- **five-letter-freq-site.AC5.1 Success:** Built page contains no external `<script src="http...">` or `<link href="http...">` tags outside Zensical's own assets

---

<!-- START_SUBCOMPONENT_A (tasks 1-3) -->
<!-- START_TASK_1 -->
### Task 1: Add Polars dependency and create directory structure

**Files:**
- Modify: `pyproject.toml` (add polars to dependencies)
- Create: `docs/css/heatmap.css` (empty placeholder)
- Create: `tests/conftest.py` (empty placeholder)

**Step 1: Add polars dependency**

```bash
uv add polars
```

**Step 2: Create directories and placeholder files**

```bash
mkdir -p docs/css docs/data docs/js tests
touch docs/css/heatmap.css tests/conftest.py tests/__init__.py
```

**Step 3: Add pytest as dev dependency**

```bash
uv add --dev pytest
```

**Step 4: Verify**

```bash
uv sync
uv run python -c "import polars; print(polars.__version__)"
```

Expected: Polars version prints without error.

**Step 5: Commit**

```bash
git add pyproject.toml uv.lock docs/css/heatmap.css docs/data/ docs/js/ tests/
git commit -m "chore: add polars dependency, pytest, and directory structure"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Implement main.py — word list loading and overall frequency computation

**Verifies:** five-letter-freq-site.AC2.1

**Files:**
- Modify: `main.py` (replace stub with frequency computation and page generation)

**Implementation:**

`main.py` should:
1. Read `/usr/share/dict/words`, filter to lines matching `^[a-z]{5}$` (lowercase only, exactly 5 chars)
2. Build a Polars DataFrame with one row per word
3. Explode each word into individual letters with their positions (1-5)
4. Use `group_by("letter").len()` to compute overall frequency counts
5. Generate `docs/index.md` containing:
   - A YAML frontmatter block (no icon)
   - `# Five-Letter Word Frequencies` heading
   - A brief intro paragraph stating the word count
   - An HTML table of overall letter frequencies sorted by descending count, with a bar-style visualisation using inline `background: linear-gradient(...)` on cells
6. Write the file to `docs/index.md`

Key Polars patterns to use:
- `pl.DataFrame({"word": words})` to create the initial frame
- `.with_columns(pl.col("word").str.split("").alias("letters"))` or similar to split into chars
- `.explode("letters")` to get one row per letter
- `.group_by("letter").len()` for overall counts
- `.sort("len", descending=True)` for ranked output

The generated `docs/index.md` should NOT include any `<script>` or `<link>` tags to external CDNs.

**Verification:**

```bash
uv run python main.py
```

Expected: `docs/index.md` is generated with an HTML frequency table. Inspect the file to verify it contains 26 letter rows.

**Commit:**

```bash
git add main.py docs/index.md
git commit -m "feat: implement overall letter frequency computation and page generation"
```
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Write tests for overall frequency correctness

**Verifies:** five-letter-freq-site.AC2.1

**Files:**
- Create: `tests/test_frequencies.py`

**Testing:**

Tests must verify:
- five-letter-freq-site.AC2.1: The sum of all overall frequency counts equals exactly 5 × word_count (since each 5-letter word contributes 5 letters)

Approach:
- Import the frequency computation logic from `main.py` (may need to refactor `main.py` to expose a function that returns the computed data, separate from the page generation)
- Call the computation function
- Assert `sum(all_counts) == 5 * word_count`
- Also verify all 26 lowercase letters are present in the output
- Spot-check: verify counts for a common letter (e.g. 'e') match `grep -o 'e' /usr/share/dict/words | wc -l` equivalent across the filtered word set

**Verification:**

```bash
uv run pytest tests/test_frequencies.py -v
```

Expected: All tests pass.

**Commit:**

```bash
git add tests/ main.py
git commit -m "test: add overall frequency sum validation"
```
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->

<!-- START_TASK_4 -->
### Task 4: Configure Zensical extra_css and verify site build

**Verifies:** five-letter-freq-site.AC1.1

**Files:**
- Modify: `zensical.toml` (uncomment and set `extra_css`)
- Modify: `docs/css/heatmap.css` (add base styles for frequency table)

**Step 1: Update zensical.toml**

In `zensical.toml`, find the commented-out `extra_css` line (currently `#extra_css = ["stylesheets/extra.css"]`) and replace it with:

```toml
extra_css = ["css/heatmap.css"]
```

Note: path is relative to `docs/` directory.

**Step 2: Add base CSS to heatmap.css**

Add minimal styles for the frequency table:
- `.freq-table` — table styling (border-collapse, width)
- `.freq-table td, .freq-table th` — padding, borders
- `.freq-bar` — the bar visualisation cell styling

Keep it minimal — later phases will extend this file.

**Step 3: Verify site builds**

```bash
uv run zensical build --clean
```

Expected: Build succeeds, `site/` directory is produced containing `index.html` with the frequency table and linked CSS.

**Step 4: Verify no external deps in built page**

```bash
grep -E 'src="https?://' site/index.html || echo "No external scripts found"
grep -E 'href="https?://' site/index.html | grep -v 'rel="canonical"' || echo "No external stylesheets found"
```

Expected: No external script or stylesheet references (Zensical's own assets are bundled).

**Step 5: Commit**

```bash
git add zensical.toml docs/css/heatmap.css
git commit -m "chore: configure Zensical extra_css and add base heatmap styles"
```
<!-- END_TASK_4 -->

<!-- START_TASK_5 -->
### Task 5: Update GitHub Actions workflow

**Verifies:** five-letter-freq-site.AC1.1 (deployment pipeline)

**Files:**
- Modify: `.github/workflows/docs.yml`

**Step 1: Update the workflow**

Replace the current build steps with:

```yaml
name: Documentation
on:
  push:
    branches:
      - master
      - main
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run python main.py
      - run: uv run zensical build --clean
      - uses: actions/upload-pages-artifact@v4
        with:
          path: site
      - uses: actions/deploy-pages@v4
        id: deployment
```

Key changes from current workflow:
- Move `actions/checkout` to first step (before `configure-pages`)
- Replace `actions/setup-python@v5` + `pip install zensical` with `astral-sh/setup-uv@v4` + `uv sync`
- Add `uv run python main.py` step before build
- Use `uv run zensical build --clean` instead of bare `zensical build --clean`

Note: AC5.1 (no external runtime deps) is verified manually by inspecting the built page, not by an automated pytest test. The shell `grep` check in Task 4 provides build-time verification.

**Step 2: Verify locally that the full pipeline works**

```bash
uv run python main.py && uv run zensical build --clean
```

Expected: Both commands succeed, `site/` contains the built page.

**Step 3: Commit**

```bash
git add .github/workflows/docs.yml
git commit -m "ci: update GitHub Actions to use uv and run main.py before build"
```
<!-- END_TASK_5 -->
