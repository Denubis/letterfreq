# Phase 4 coherence / proleptic notes

**Phase:** 4 — reference-table rendering (`letterfreq.render` module + `.ref-pair` CSS).
**BASE_SHA:** `f81f5cc` → **HEAD_SHA:** post-`bc14e36` plus the 768px breakpoint fix.
**Code review:** APPROVED with 2 Minors (both fixed at `bc14e36`): plan-doc grep-count off-by-one, and letter-cell HTML escape consistency.
**Proleptic challenge:** three concerns raised; #1 fixed, #2 resolved by reading code, #3 deferred to Phase 5.

## Concerns raised and dispositions

### 1. `.ref-pair` stacking breakpoint was 720px, not aligned with Material's 768px nav collapse — RESOLVED

**Concern:** The appended `.ref-pair` CSS used `@media (max-width: 720px)`. The parent Zensical/Material theme collapses its nav drawer at 768px. This created a 48px viewport window (720-768px) where the content pair was already stacked single-column but the nav was still consuming horizontal space — visual compression, not a hard break.

**Disposition (user, 2026-04-19):** Match the theme's breakpoint.

**Resolution:** Updated the media query in both `docs/css/heatmap.css` and the source block in `phase_04.md` from `720px` to `768px`. The switch from two-column to single-column now happens at exactly the same viewport width where the nav drawer collapses.

### 2. Label column lacks `data-value` — RESOLVED (NO DEFECT)

**Concern:** The bigram/trigram/letter label cells emit `<td class="freq-letter">{escape(text)}</td>` without a `data-value` attribute. If `docs/js/sort-tables.js` required every sortable column to have `data-value`, click-to-sort on the label column would silently break on /ten/.

**Disposition:** Read `docs/js/sort-tables.js`. The script's sort routine calls `getAttribute("data-value")` which returns `null` when absent, `parseFloat(null)` yields `NaN`, and the `isNaN` branch falls through to `textContent.trim()` with `localeCompare`. Alphabetical sort of the label column works correctly via the JS's own fallback path. No code change needed.

**Latent concern (not a Phase 4 defect):** `localeCompare` without an explicit locale argument uses the browser default. For the current a-z-only corpus this is deterministic (ASCII lexicographic), but any future table emitting non-ASCII labels would inherit locale-dependent ordering. Not in scope for the ten-letter page.

### 3. Phase 5 transparency-column scoping for the positional-endpoint ranking — DEFERRED to Phase 5

**Concern:** `render_first_last_pair` pads to 26 rows per side regardless of frequency (per DR8). This is correct and informative for the reference tables. But the Phase 5 *ranking* table for the positional-endpoint score will, per AC6.5, show "first-letter and last-letter columns plus the score". If a word's positional score is dominated by one good endpoint and one near-zero endpoint (e.g., `xylophones` — 'x' is rare as a first letter), a letter-only column hides the asymmetry and could make two visually-similar letters look equally contributive when one is near-zero.

**Disposition (user, 2026-04-19):** Deferred to Phase 5.

**Phase 5 pickup:** before finalising the positional-endpoint ranking table, decide:
- Show letters only (current AC6.5 interpretation) — simplest, but hides per-letter rate asymmetry.
- Show letters with rates alongside (e.g., `x (0.001) + s (0.089)`) — transparent but wordy.
- Show letters colour-coded by rate magnitude (via heatmap CSS) — compact and visually honest but relies on colour perception.
- Some hybrid (letters + total score only, with a tooltip showing per-letter breakdown) — feature-scoped to JS.

Write up the decision in the Phase 5 design/plan addendum. If AC6.5 needs clarification, update the design plan before Phase 5 commits code.

## Accumulated deferred items (roll-up)

Carrying forward:

- **Phase 1** (for Phase 7 pickup): upstream SHA pin / reproducibility claim; JS fetch-path regression guard; glossary type-vs-token clarification; `zensical build --clean` smoke test; TODO cleanup, main.py docstring, arch-doc tense + corpus counts.
- **Phase 2** (Phase 6 plan-writing + Phase 7): `main_ten.py` denominator must match the regression-guard pattern; corpus no-empty-lines assertion.
- **Phase 3** (Phase 5): score-column labelling to clarify non-cross-table comparability; if Phase 5 surfaces silent-zero failure on `letter_score`/`bigram_score` with short input, add matching length guards.
- **Phase 4** (Phase 5): resolve transparency-column design for positional-endpoint ranking before committing its renderer.
