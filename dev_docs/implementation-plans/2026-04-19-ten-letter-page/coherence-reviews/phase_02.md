# Phase 2 coherence / proleptic notes (deferred to Phase 7 pickup)

**Phase:** 2 — `letterfreq` package, reference-frequency module.
**BASE_SHA:** `b73759d` → **HEAD_SHA:** `31e1c42`.
**Code review:** APPROVED, zero issues (2026-04-19).
**Proleptic challenge:** four concerns raised, all deferred by user decision.

## Concerns raised and dispositions

### 1. `to_rates` behaviour on `total <= 0` — ACCEPTED AS-IS

**Concern:** The guard `if total <= 0: return {key: 0.0 for key in counts}` treats negative totals identically to zero. An adversarial reviewer argued `total < 0` should raise `ValueError` rather than silently return zeros, on the grounds that a negative total is almost certainly a caller logic error rather than a recoverable data condition.

**Disposition (user, 2026-04-19):** The guard is fine. Keep the current behaviour — zero-fill on `total <= 0`. No code change.

**Why the decision is defensible:** `to_rates` is called by rate-display code, not safety-critical. An empty corpus produces `total = 0` legitimately. A caller passing a negative total is almost certainly computing `total` wrong (e.g., subtracting when they meant to sum), and zero-fill degrades gracefully rather than crashing the page build. The pure-functional contract is "count → rate or zero"; introducing an exception path complicates the FCIS discipline for a case that has no legitimate trigger.

**Future reviewer:** If this surfaces as an actual bug, reconsider. Until then, do not change.

### 2. `min_length=4` trigram default — population validity — ACCEPTED AS-IS

**Concern:** DR3's justification for `min_length=4` is "avoids 3-letter start/end double-count". It does not justify whether the resulting start/end trigram *weight distribution* (pooled across all 4+ letter words in the 3-10 letter baseline) is the right population for scoring 10-letter words. Short-word trigrams predominate in English and may shift the distribution away from what is informative for 10-letter scoring.

**Disposition (user, 2026-04-19):** `min 4` is fine. Keep the current default.

**Why the decision is defensible:** The baseline corpus is explicitly chosen as "common English 3-10 letter words" because it is the most stable and inclusive reference available. Restricting to longer words would narrow the corpus, reduce statistical power, and introduce a different bias (favouring rare longer words over common shorter ones). The scoring goal is "which 10-letter words use the most English-common trigrams", and English-common is well-approximated by the 3-10 pool.

**Future reviewer:** If scoring results look biased toward short-word phonology, consider `min_length=5` or a length-weighted average. For now, leave as DR3 specifies.

### 3. Empty-string guard in `first_letter_counts` / `last_letter_counts` untested against production data — DEFERRED to Phase 7

**Concern:** The `if word:` guard in both functions is documented as defensive. The integration-test fixture pre-filters empty lines via `if w` in `baseline_words`, so the guard is never exercised against the actual file. If `scripts/build_corpora.py` produces a corpus with empty lines, the guard silently swallows them instead of raising.

**Disposition (user, 2026-04-19):** Defer. Phase 7 (`tests/test_corpora.py` per plan) is scheduled to assert corpus shape invariants, including no-empty-lines. If Phase 7 adds that assertion, the Phase 2 guard becomes belt-and-braces rather than load-bearing, which is acceptable.

**Phase 7 pickup:** confirm that `tests/test_corpora.py` (or equivalent) includes `assert all(line for line in content.splitlines())` or structurally equivalent against `data/words_3_to_10.txt` and `data/words_10.txt`. If absent, add it.

### 4. Regression-guard test documents but does not enforce the Phase 6 denominator bug — DEFERRED to Phase 6

**Concern:** `test_to_rates_trigram_denominator_pattern_sums_to_one` demonstrates that passing `total=len(all_words)` for a filtered trigram count is wrong, and that `total=sum(counts.values())` is right. The test passes on `to_rates` in isolation; it does not mechanically prevent `main_ten.py` (Phase 6) from making the wrong call. It is a social-layer control.

**Disposition (user, 2026-04-19):** Defer to Phase 6 plan writing.

**Phase 6 pickup:** when Phase 6 is about to be executed, the implementer must be reminded (in the phase file or by the orchestrator) to:
- Read this regression-guard test before writing rate-calculation calls.
- Ensure every `to_rates(counts, total=...)` call in `main_ten.py` uses `sum(counts.values())` (or an equivalent contributor-count) when the counts exclude some input words.
- Add a test in `tests/test_main_ten.py` (or equivalent) that exercises the actual `main_ten.py` rate path and asserts the rate dicts sum to 1.0, so the denominator bug is caught mechanically in context, not just in isolation.

## Phase 1 carry-over reminder

Phase 1 coherence findings (separate file, `phase_01.md`) also defer to Phase 7. The deferred items now accumulating:

- Phase 1 #1 (pin upstream to SHA or soften reproducibility claim)
- Phase 1 #2 (regression guard: JS `fetch("data/bigrams.json")` path aligns with `docs/five/data/` location)
- Phase 1 #3 (glossary: type-vs-token frequency clarification)
- Phase 1 #4 (`zensical build --clean` smoke test)
- Phase 1 Low findings (TODO in `docs/index.md`, stale `main.py` module docstring, architecture-doc tense refresh + fill in corpus counts 45,872 / 248,010)
- **Phase 2 #3** (corpus no-empty-lines assertion in Phase 7 tests)
- **Phase 2 #4** (Phase 6 must wire `main_ten.py` denominator against the regression-guard pattern)
- **Phase 2 #1, #2** (resolved by user decision — no Phase 7 action required)

When Phase 7 is planned and executed, work through this accumulated list along with whatever Phase 7's own plan requires.
