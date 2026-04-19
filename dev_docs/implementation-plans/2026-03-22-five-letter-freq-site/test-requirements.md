# Test Requirements — five-letter-freq-site

Mapping of each acceptance criterion to its verification method. Cross-referenced with implementation phases 1-5.

---

## five-letter-freq-site.AC1: Site builds and deploys

### five-letter-freq-site.AC1.1 — `uv run zensical build --clean` exits 0 and produces `site/` directory

- **Verification:** Automated
- **Test type:** Integration
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** Runs `uv run zensical build --clean` via `subprocess.run`, asserts exit code 0 and that `site/` directory exists and contains `index.html`.
- **Phase coverage:** Phase 1, Task 4 (build verification). The implementation plan calls for a shell-level check during Task 4; this should be codified as a pytest integration test.

### five-letter-freq-site.AC1.2 — GitHub Actions workflow completes and site is accessible at Pages URL

- **Verification:** Human
- **Justification:** Requires a live GitHub Actions run and network access to the deployed Pages URL. Cannot be reproduced in a local test environment — depends on GitHub infrastructure, repository secrets, and DNS propagation.
- **Verification approach:**
  1. Push to `main` branch.
  2. Confirm the Actions workflow at `.github/workflows/docs.yml` completes with a green check.
  3. Visit the Pages URL and confirm the page loads with frequency content.

---

## five-letter-freq-site.AC2: Frequency data is correct

### five-letter-freq-site.AC2.1 — Overall frequencies sum to 5 x word_count

- **Verification:** Automated
- **Test type:** Unit
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** Calls the overall frequency computation function from `main.py`. Asserts `sum(all_letter_counts) == 5 * word_count`. Also verifies all 26 lowercase letters are present in the output.
- **Phase coverage:** Phase 1, Task 3.

### five-letter-freq-site.AC2.2 — Unigram positional counts per position sum to word_count

- **Verification:** Automated
- **Test type:** Unit
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** Calls the unigram computation function from `main.py`. For each of the 5 positions, asserts `sum(letter_counts_at_position) == word_count`. Verifies all 26 letters have entries at each position.
- **Phase coverage:** Phase 2, Task 3.

### five-letter-freq-site.AC2.3 — Bigram counts for positions 1-2 sum to word_count

- **Verification:** Automated
- **Test type:** Unit
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** Calls the bigram computation function from `main.py`. Sums all cell counts in the positions 1-2 grid and asserts the total equals `word_count`. Repeats for at least one other pair (e.g. positions 4-5) as a sanity check.
- **Phase coverage:** Phase 3, Task 3.

### five-letter-freq-site.AC2.4 — Trigram gap completions for a known pair match manual grep verification

- **Verification:** Automated
- **Test type:** Unit
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** For a specific trigram combination (e.g. `gap1_win123` with known letters at positions 2 and 3), the test independently counts matching words from the filtered word list using a regex (equivalent to `grep -c '^.he..$'`) and asserts the trigram gap completions sum to that count. Also verifies the trigram data structure has exactly 9 top-level keys.
- **Phase coverage:** Phase 5, Task 4.

---

## five-letter-freq-site.AC3: Bigram drill-down

### five-letter-freq-site.AC3.1 — Clicking a bigram row header expands to show neighbour frequency bars for that letter at that position

- **Verification:** Automated (data) + Human (interaction)
- **Test type:** Unit (data correctness)
- **Test file:** `tests/test_frequencies.py`
- **What the test checks (automated):** Calls the neighbour frequency computation function for a known letter at a known position. Asserts the returned distribution counts are consistent with the bigram data — specifically, that the sum of neighbour counts equals the letter's total occurrences at that position (cross-checked against unigram data).
- **Human verification:** Open the built site, expand a bigram grid, click a row header letter, and confirm the drill-down appears with frequency bars.
- **Justification for human component:** The automated test verifies data correctness but cannot verify that the `<details>` HTML renders and expands correctly in a browser. A headless browser e2e test could cover this but is out of scope for the current stack.
- **Phase coverage:** Phase 4, Task 3.

### five-letter-freq-site.AC3.2 — Edge positions (1, 5) show only one neighbour; middle positions show two

- **Verification:** Automated
- **Test type:** Unit
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** Calls the neighbour computation function for position 1 and asserts only a right-neighbour distribution is returned (1 direction). Calls it for position 5 and asserts only a left-neighbour distribution (1 direction). Calls it for position 3 and asserts both directions are returned (2 directions).
- **Phase coverage:** Phase 4, Task 3.

### five-letter-freq-site.AC3.3 — Row header for a letter with zero occurrences at that position shows empty or absent drill-down

- **Verification:** Automated
- **Test type:** Unit
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** Identifies (empirically or synthetically) a letter with zero occurrences at a given position. Calls the neighbour computation function and asserts it returns empty distributions. The HTML generator is expected to omit the `<details>` element for such rows.
- **Phase coverage:** Phase 4, Task 3.

---

## five-letter-freq-site.AC4: Trigram click-to-expand

### five-letter-freq-site.AC4.1 — Clicking a non-empty trigram cell shows sorted completion list with counts and percentages

- **Verification:** Automated (data) + Human (interaction)
- **Test type:** Unit (data structure)
- **Test file:** `tests/test_frequencies.py`
- **What the test checks (automated):** Verifies the trigram JSON data structure has 9 top-level keys with nested dicts. For a known non-empty cell, asserts completion entries exist and are non-zero. Verifies counts match independent grep-based verification (covered by AC2.4).
- **Human verification:** Open the built site, scroll to the trigram section, click a coloured cell, and confirm a sorted completion list appears below the grid showing letters, counts, and percentage bars.
- **Justification for human component:** The click-to-expand behaviour is driven by `docs/js/trigram-expand.js`. Verifying that the JavaScript correctly fetches JSON, renders the completion list, sorts it, and computes percentages requires browser execution. No headless browser testing framework is in the project stack.
- **Phase coverage:** Phase 5, Tasks 3-4.

### five-letter-freq-site.AC4.2 — Clicking an empty cell shows "No completions" or similar (no error)

- **Verification:** Automated (data) + Human (interaction)
- **Test type:** Unit (data structure)
- **Test file:** `tests/test_frequencies.py`
- **What the test checks (automated):** Looks up a known-empty pair in the trigram data and asserts the key is missing (None / KeyError). This confirms the data layer correctly represents empty cells, which the JS interprets as "No completions".
- **Human verification:** Open the built site, click an empty (uncoloured) trigram cell, and confirm either nothing happens (no event listener on `.empty` cells) or a "No completions" message appears. Confirm no JavaScript error in the browser console.
- **Justification for human component:** Same as AC4.1 — the empty-cell handling is a JS runtime concern.
- **Phase coverage:** Phase 5, Tasks 3-4.

---

## five-letter-freq-site.AC5: No external runtime dependencies

### five-letter-freq-site.AC5.1 — Built page contains no external `<script src="http...">` or `<link href="http...">` tags outside Zensical's own assets

- **Verification:** Automated
- **Test type:** Integration
- **Test file:** `tests/test_frequencies.py`
- **What the test checks:** After building the site, reads `site/index.html` and scans for `<script src="http` and `<link href="http` patterns. Asserts zero matches (excluding any `rel="canonical"` links which are metadata, not runtime dependencies). This codifies the shell `grep` check from Phase 1, Task 4 into a repeatable pytest assertion.
- **Phase coverage:** Phase 1, Task 4 (shell check). Should be promoted to a formal pytest test.

---

## Coverage Matrix

| AC | Criterion | Automated | Human | Test File | Phase |
|----|-----------|-----------|-------|-----------|-------|
| AC1.1 | Build exits 0, produces `site/` | Yes (integration) | No | `tests/test_frequencies.py` | 1 |
| AC1.2 | GitHub Actions deploys to Pages | No | Yes | N/A | 1 |
| AC2.1 | Overall freq sums to 5 x word_count | Yes (unit) | No | `tests/test_frequencies.py` | 1 |
| AC2.2 | Unigram per-position sums to word_count | Yes (unit) | No | `tests/test_frequencies.py` | 2 |
| AC2.3 | Bigram 1-2 sums to word_count | Yes (unit) | No | `tests/test_frequencies.py` | 3 |
| AC2.4 | Trigram completions match grep | Yes (unit) | No | `tests/test_frequencies.py` | 5 |
| AC3.1 | Drill-down shows neighbour bars | Yes (data) | Yes (UI) | `tests/test_frequencies.py` | 4 |
| AC3.2 | Edge positions show 1 neighbour | Yes (unit) | No | `tests/test_frequencies.py` | 4 |
| AC3.3 | Zero-occurrence letter: empty drill-down | Yes (unit) | No | `tests/test_frequencies.py` | 4 |
| AC4.1 | Click non-empty cell: completion list | Yes (data) | Yes (UI) | `tests/test_frequencies.py` | 5 |
| AC4.2 | Click empty cell: no error | Yes (data) | Yes (UI) | `tests/test_frequencies.py` | 5 |
| AC5.1 | No external script/link tags | Yes (integration) | No | `tests/test_frequencies.py` | 1 |

## Human Verification Summary

Three criteria require human verification, all due to the same gap: no headless browser testing in the project stack.

| AC | What to verify manually | When |
|----|------------------------|------|
| AC1.2 | GitHub Actions green, Pages URL loads | After first push with workflow changes |
| AC3.1 | `<details>` drill-down expands in browser | After Phase 4 |
| AC4.1, AC4.2 | JS click-to-expand works, empty cells handled | After Phase 5 |

If a headless browser framework (e.g. Playwright) were added in the future, AC3.1, AC4.1, and AC4.2 could be fully automated as e2e tests. AC1.2 would remain human-verified as it depends on GitHub infrastructure.
