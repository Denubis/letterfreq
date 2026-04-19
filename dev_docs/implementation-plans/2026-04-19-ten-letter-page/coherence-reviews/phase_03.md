# Phase 3 coherence / proleptic notes

**Phase:** 3 — `letterfreq` package, scoring module.
**BASE_SHA:** `0c796d5` → **HEAD_SHA:** `9910bc8`.
**Code review:** APPROVED with 1 Minor (plan-doc off-by-one — fixed at `db20abe`).
**Proleptic challenge:** three concerns raised; two addressed with code changes, one deferred to Phase 5.

## Concerns raised and dispositions

### 1. NaN / inf propagation through `top_n_by_score` — RESOLVED (`9910bc8`)

**Concern:** If any rate dict contains NaN or inf (e.g., from an upstream 0/0 division bug), `sort` on `(-score, word)` tuples is non-deterministic — Python's Timsort does O(n log n) comparisons but NaN comparisons are always False, so the sort outcome is implementation-defined for inputs containing non-finite values. Exposure is narrow (Phase 2's `to_rates` already guards `total <= 0`), but silent misordering is a worse failure mode than explicit error.

**Disposition (user, 2026-04-19):** Add an explicit finite-check before the sort.

**Resolution:** `top_n_by_score` now iterates over the scored list and raises `ValueError` if any score fails `math.isfinite`. Tests `test_top_n_by_score_rejects_nan_score` and `test_top_n_by_score_rejects_inf_score` exercise both paths.

### 2. `trigram_score` / `positional_endpoint_score` length assumptions not runtime-enforced — RESOLVED (`9910bc8`)

**Concern:** Plan docstrings said "Assumes len(word) >= 3" (trigram) and "Assumes len(word) >= 1" (positional endpoint), but the implementation did not enforce these. `trigram_score` on a 2-letter word would compute `word[:3] + word[-3:]` — both slice expressions return the whole 2-letter word — yielding two rate-dict lookups on a 2-letter key, both silently defaulting to 0.0 via `dict.get`. The failure mode is silent-wrong-answer, not an exception. A future Phase 5 rendering call site (not yet written) that accepts arbitrary `Iterable[str]` could bypass Phase 6's corpus-filtering and pass shorter words without signal.

**Disposition (user, 2026-04-19):** Add explicit `ValueError` guards at the entry points.

**Resolution:**
- `trigram_score`: `if len(word) < 3: raise ValueError(f"trigram_score requires len(word) >= 3, got {len(word)}: {word!r}")`
- `positional_endpoint_score`: `if not word: raise ValueError("positional_endpoint_score requires a non-empty word")`
- Tests `test_trigram_score_rejects_short_word` and `test_positional_endpoint_score_rejects_empty_word` exercise both guards.

Docstrings updated from "Assumes..." to "Raises ValueError if...".

**Note on scope:** `letter_score` and `bigram_score` also have implicit length assumptions (both return 0.0 cleanly on short input, but that is still silent-wrong-answer for the module's 10-letter purpose). The proleptic did NOT flag these, and the user's instruction was "add length guards" without enumeration — interpreted narrowly as the two flagged functions. If Phase 5 tests surface the same silent-zero failure mode in `letter_score`/`bigram_score`, add matching guards at that point.

### 3. Scores across the four ranking tables are not cross-comparable — DEFERRED to Phase 5

**Concern:** `letter_score` (distinct letters only, up to 10 terms), `bigram_score` (9 terms, counting repeats), `trigram_score` (2 terms), and `positional_endpoint_score` (2 terms) are each internally meaningful numbers but have different denominators and term counts. A reader comparing a letter-coverage score of 0.42 against a bigram score of 0.38 across tables would be comparing different quantities. DR1 justified four independent tables (not a composite score) on these grounds, but the display does not warn the reader against cross-table score comparison.

**Disposition (user, 2026-04-19):** Deferred to Phase 5 (rendering module). Not a Phase 3 code issue.

**Phase 5 pickup:** when Phase 5 is planned, decide:
- Whether the score column header should include a per-table unit label (e.g., "letter-coverage sum", "bigram-rate sum") to clarify non-comparability.
- Whether a shared footnote or preface note on the ten-letter page should explicitly state that scores are within-table quantities only, not cross-table.
- Whether scores should be rendered with different decimal precision per table, to deter accidental cross-reading.

None of these require code changes to `scoring.py`; they are rendering/labelling decisions.

## Accumulated deferred items (roll-up)

Carrying forward from Phases 1 and 2, plus Phase 3:

- **Phase 1 items** (for Phase 7 coherence-review pickup): pin upstream SHA or soften reproducibility claim; JS fetch-path regression guard; glossary type-vs-token clarification; `zensical build --clean` smoke test; Low findings (TODO cleanup, main.py docstring, arch-doc tense + corpus counts).
- **Phase 2 items**: corpus no-empty-lines assertion (Phase 7); `main_ten.py` denominator must match the regression-guard pattern (Phase 6 plan writing).
- **Phase 3 item**: score-column labelling and cross-table comparability note (Phase 5 plan writing).
- **Phase 3 deferred scope**: if Phase 5 surfaces silent-zero failure on `letter_score`/`bigram_score` with short input, add matching length guards.
