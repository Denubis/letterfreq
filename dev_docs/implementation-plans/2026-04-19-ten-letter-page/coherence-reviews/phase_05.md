# Phase 5 coherence / proleptic notes

**Phase:** 5 — ranking-table rendering (four ranking renderers + `_ranking_thead` helper in `letterfreq.render`).
**BASE_SHA:** `b3364bb` → **HEAD_SHA:** `d908e15`.
**Code review:** APPROVED after one fix cycle (1 Critical + 2 Important → all resolved at `d908e15`).
**Proleptic challenge:** four concerns raised, all deferred to Phase 6 plan-writing.

## Phase 5 resolved findings (for the record)

### Review-loop fixes landed at `d908e15`

1. **Lambda style (reviewer flagged as Critical; downgraded to consistency fix since ruff is not project-adopted):** `render_letter_ranking` and `render_bigram_ranking` had `score_fn = lambda word: ...` assignments, inconsistent with `render_trigram_ranking` and `render_positional_ranking` which already used nested `def score_fn`. All four now use nested `def`. `lambda l:` renamed to `lambda ch:` to avoid ambiguous `l` variable name.

2. **Bigram transparency test (Important):** original test asserted only `"st" in html` for the word `"statistics"` — did not discriminate contribution-ordering from raw-rate ordering because both would have placed `"st"` first. Strengthened to use word `"ababababcd"` with rates where contribution-order and raw-rate-order disagree (`ab` rate 0.1 × 4 counts = contribution 0.4; `cd` rate 0.25 × 1 count = contribution 0.25). Test now asserts `"ab, cd" in html` (correct contribution-ordered output) AND `"cd, ab" not in html` (would appear if implementation were raw-rate-ordered). Now falsifiable.

3. **Letter-ranking transparency test (Important):** original test used uniform rates and asserted presence only — did not verify the sort-order requirement from AC6.1's transparency clause. Strengthened to use non-uniform rates `{a: 0.5, b: 0.3, c: 0.1, d: 0.05, e: 0.02, others: 0.001}` and asserts the exact substring `"a b c d e"` appears in the HTML — verifies both presence and descending-rate ordering.

### User-chosen plan deviation

**Score column labels disambiguated** per Phase 3/4 coherence decision: `Score (letter)` / `Score (bigram)` / `Score (trigram)` / `Score (endpoint)` instead of uniform `"Score"`. This was the only deviation from verbatim plan code and applies to all four ranking renderers. Resolves the "scores across tables are not cross-comparable" concern accumulated from Phase 3.

## Concerns raised and deferred to Phase 6 plan-writing

### 1. Test/code divergence for the denominator regression pattern — DEFERRED to Phase 6

**Concern:** Phase 6 Task 3's planned tests re-compute rate dicts inside the test rather than asserting against `generate_page`'s own denominator choices. If the Phase 6 implementer introduces the denominator bug that Phase 2's `test_to_rates_trigram_denominator_pattern_sums_to_one` regression test warned against, the new `test_main_ten.py` would not mechanically catch it — the test is testing the same denominator logic it expects `generate_page` to use, rather than the actual `generate_page` output.

**Disposition (user, 2026-04-19):** Defer.

**Phase 6 pickup:** factor a `_compute_rates` helper (or equivalent) that takes `counts` and returns the rate dicts. Both `generate_page` and the test must call this helper. Alternatively, have `generate_page` return its intermediate rate dicts alongside the page string so tests can introspect them. Either way, the denominator choice must be testable at the call-site level, not just replicated in test setup. This is the structural control that Phase 2's regression-guard was originally meant to enable.

### 2. "Top 3" bigram transparency needs a concrete visual-trigger criterion — DEFERRED to Phase 6

**Concern:** The plan defends "top 3 contributors" on the grounds that a 10-letter word has at most 9 distinct bigrams. For a word with highly concentrated contributions (e.g., `er` appearing 4 times dominates), top-3 is plenty. For a word with 9 nearly-equal contributions, top-3 hides 67% of the score's justification. The Phase 6 plan says to "spot-check" the tables visually but provides no threshold for deciding when 3 is inadequate.

**Disposition (user, 2026-04-19):** Defer.

**Phase 6 pickup:** before visual spot-check, write a named threshold into the Phase 6 plan. Suggested criterion: if any top-10 ranked word's top-3 bigram contributions sum to less than 50% of its total bigram score, increase the transparency cap to top-5 in `render_bigram_ranking`. Alternatively, write an automated assertion that runs during the build: compute the top-3 contribution ratio for the top-20 words and fail the build if it falls below a threshold. Without a forcing function, the "good enough" decision will rubber-stamp the first pass.

### 3. Duplicate words in `words_10.txt` are unguarded — DEFERRED to Phase 6 / Phase 7

**Concern:** The current Phase 7 corpus-test spec checks `^[a-z]{10}$` but does NOT assert `len(words) == len(set(words))`. If `scripts/build_corpora.py` ever emits duplicates (unlikely but possible if upstream data contains them), Phase 5's `top_n_by_score` would happily rank the same word twice. No test catches this; the ranking-table HTML would silently show two identical rows with the same score.

**Disposition (user, 2026-04-19):** Defer.

**Phase 6/7 pickup:** add EITHER:
- Phase 6: defensive dedupe in `load_words` — `return list(dict.fromkeys(words))` (preserves order, two-line change) — making the system structurally correct regardless of corpus file state.
- Phase 7: uniqueness assertion in `test_corpora.py` — `assert len(words) == len(set(words))`. Catches regressions in `scripts/build_corpora.py` but does not protect runtime if the corpus file is hand-edited.

Defense-in-depth favours both. Pick at least one.

### 4. Reference-table "Per-word rate" vs scoring "per-occurrence rate" — DEFERRED to Phase 6 prose

**Concern:** The reference letter-frequency table's rate column is labelled `Per word` (count / word_count — roughly "fraction of words containing this letter"). The ranking-table letter-score sums `letter_rates[ch]` where `letter_rates` comes from `to_rates(counts, total=sum(counts.values()))` — the per-occurrence rate (count / total letter occurrences). These are different numbers for the same letter. A reader who looks up `e` in the reference table and sees 0.38 ("38% of words contain e"), then looks at a word's letter-score showing `e` contributing 0.13 (per-occurrence rate), has no way to reconcile those.

**Disposition (user, 2026-04-19):** Defer to Phase 6 prose.

**Phase 6 pickup:** add a one-sentence reconciling note under the ranking sections (or in a shared preface) clarifying that "per-word rate" in the reference tables and "per-occurrence rate" in the scoring formula are different quantities over the same baseline corpus — the reference shows how many words the letter appears in; the score uses how common the letter is relative to all letter occurrences. OR: align the two by having the reference tables show per-occurrence rate too. OR: accept the confusion if the Phase 6 author judges the visual signal to be more important than the numeric precision.

## Accumulated deferred items (roll-up heading into Phase 6)

Carrying forward from all prior phases into Phase 6's plan adaptation:

- **Phase 1** (for Phase 7 pickup): upstream SHA pin or softened reproducibility claim; JS fetch-path regression guard; glossary type-vs-token clarification; `zensical build --clean` smoke test; Low findings (TODO cleanup, `main.py` docstring, arch-doc tense + corpus counts).
- **Phase 2** (Phase 6 + Phase 7): `main_ten.py` denominator must use the regression-guard pattern (now concretised as the `_compute_rates` factoring in concern #1 above); corpus no-empty-lines assertion (Phase 7).
- **Phase 3** (Phase 5 — RESOLVED): score-column labelling via `Score (letter/bigram/trigram/endpoint)`.
- **Phase 4** (Phase 5 — RESOLVED): transparency-column design for positional ranking — letters only, per-user decision.
- **Phase 5** (Phase 6 plan-writing): denominator test structure (#1); top-3 bigram transparency threshold (#2); duplicate-word guard (#3); per-word vs per-occurrence rate prose (#4).

## Recommended Phase 6 plan-writing preamble

Before the Phase 6 implementor is dispatched, read this file and decide:
1. **Factor `_compute_rates` out of `generate_page`** so tests can call it directly.
2. **Write a top-3-vs-top-5 trigger criterion** into the Phase 6 plan before any visual spot-check happens.
3. **Add `dict.fromkeys` dedupe to `load_words`** AND/OR uniqueness assertion in Phase 7 corpus tests.
4. **Add a one-sentence rate-reconciliation note** to the Phase 6 page prose.

All four are small, cheap, and forestall re-work after Phase 6's first rendered page is reviewed.
