# Coherence Review: Phase 1 — Corpus generation and site restructuring

Reviewer: Claude Opus 4.7 (1M context)
Date: 2026-04-19
Phase file: /home/brian/llm/letterfreq/dev_docs/implementation-plans/2026-04-19-ten-letter-page/phase_01.md
Design plan: /home/brian/llm/letterfreq/dev_docs/design-plans/2026-04-19-ten-letter-page.md
Diff range: 26c5c61..346e7f4 (6 commits)

## Conformance

The implementation matches the design's architectural intent for this phase. Checked against DoD items 1, 4, 5 (the Phase-1-relevant slice) and against the `Components` / `Done when` clauses of Phase 1:

- Three URLs present in built site (`site/index.html`, `site/five/index.html`, `site/ten/index.html`). Confirmed by `uv run zensical build --clean` producing each route.
- `zensical.toml` has explicit `nav` block with Home / Five-letter / Ten-letter entries (lines 47–51) — matches DoD and AC7.4.
- Five-letter page moved to `docs/five/` with co-located `docs/five/data/bigrams.json` and `trigrams.json`; JS `fetch("data/bigrams.json")` and `fetch("data/trigrams.json")` paths are preserved as bare-relative and resolve under `/five/` — matches the design's explicit call-out in Components.
- `main.py` path constants updated to `FIVE_DIR` and `DATA_DIR = FIVE_DIR / "data"` — matches phase file's exact edit. `WORD_FILE` left untouched (correct — existing five-letter corpus).
- `pyproject.toml` pin is `zensical>=0.0.33` — matches DoD 4 and design plan.
- New corpora committed: `data/words_10.txt` (45,872 lines) and `data/words_3_to_10.txt` (248,010 lines). Existing `data/words.txt` (15,921 lines) is byte-unchanged by the diff.
- `scripts/build_corpora.py` + empty `scripts/__init__.py` present at the specified paths.

No drift or erosion found in what was built relative to the phase spec.

One structural observation (not a defect): the design plan's "Phase 1 Components" list includes bullet _"Move `docs/data/bigrams.json` and `docs/data/trigrams.json` → `docs/five/data/...`"_. The diff shows those moves as pure renames (`docs/{ => five}/data/bigrams.json`, `0` lines changed) — git-preserved history, matches intent.

## Traceability

Phase 1 covers AC7.* (build + site structure) and AC8.* (corpus invariants). No functional ACs (AC1–AC6, AC10) are in scope.

| AC | Design requirement | Built artifact | Verification in this phase |
|----|--------------------|----------------|---------------------------|
| AC7.1 | `zensical build` succeeds at >=0.0.33 | `pyproject.toml` L9, `uv.lock` refreshed | Operational: build completed in 0.30s against committed code |
| AC7.2 | `/five/` renders with drill-downs working | `docs/five/index.md`, `docs/five/data/{bigrams,trigrams}.json`, JS unchanged | **Manual visual** — not automated in this phase; deferred per phase file |
| AC7.3 | `/` shows landing page with both links | `docs/index.md` has `[Five-letter words](five/)` and `[Ten-letter words](ten/)` | Content presence verified |
| AC7.4 | `zensical.toml` nav exposes Home/Five/Ten | `zensical.toml` L47–51 | Text presence verified |
| AC7.5 | Dark/light toggle + instant nav work | `zensical.toml` palette + features `navigation.instant` unchanged | **Manual visual** — deferred |
| AC8.1 | `words_10.txt` non-empty; every line `^[a-z]{10}$` | `data/words_10.txt` 45,872 lines | `awk 'length!=10 || !/^[a-z]+$/' data/words_10.txt` returns empty — passes |
| AC8.2 | `words_3_to_10.txt` non-empty; every line `^[a-z]{3,10}$` | `data/words_3_to_10.txt` 248,010 lines | `awk` check passes |
| AC8.3 | `data/words.txt` unchanged, ≥15,000 lines, `^[a-z]{5}$` | 15,921 lines, `awk` check passes | Git diff of range shows file absent from changes — confirmed unmodified |

**Candidate fitness functions / test requirements (for Phase 7's `test_corpora.py`):**
1. AC8.1, AC8.2, AC8.3 are all trivially automatable with `re.fullmatch` + line-count assertions. Phase file § "Tests for AC8 invariants are written in Phase 7" already schedules this. Do not re-flag this as a Phase 1 coherence finding — the automation is already in the plan.
2. AC7.1 (build succeeds) is automatable as a `subprocess.run(["uv", "run", "zensical", "build", "--clean"], check=True)` smoke test. Not currently planned in Phase 7. Recommend considering adding — flagged as Medium.

**Traceability gaps (relative to what *this phase* was supposed to deliver):**
- None. Every Phase-1 AC has a corresponding artifact on disk.
- AC7.2 and AC7.5 (drill-downs, dark/light, instant nav) have code in place but no automated guard; they rely on later manual visual inspection. This matches what the phase file declared explicitly, so it is not a coherence defect — but note: the first truly automated regression check for drill-down behaviour only exists as browser-eye inspection. If a future refactor breaks the bare-relative `fetch("data/bigrams.json")` resolution, nothing in the test suite will catch it. **Candidate test requirement:** a minimal static check that the JS fetch path is bare-relative AND that the corresponding JSON file exists at `docs/five/data/` — trivial `pathlib` + regex, would be a fitness function for AC7.2.

## Baked-In Assumptions

Decisions the implementation made where the design plan and/or phase file were silent. Rated by forward impact.

### 1. Upstream download timeout (60 seconds) — **benign**
- **Design said:** Silent. Phase file also silent. Code review (commit `346e7f4`) added `timeout=60` after the initial commit.
- **Implementation chose:** 60 seconds.
- **Forward impact:** None. One-shot helper re-run only when corpus is regenerated. 60 s is generous for a ~4 MB fetch from GitHub raw. Regeneration is manual and the failure mode (timeout raised) is loud and obvious.

### 2. Output file dedup strategy — **benign (now)**
- **Design said:** Silent on dedup.
- **Implementation chose:** Initially `sorted({w for w in words if ...})` — set-based dedup. After code review, switched to generator comprehension with justifying comment ("words_alpha.txt is already deduplicated upstream; list comprehension suffices").
- **Forward impact:** None _under the stated assumption_. **This is the notable bit:** the assumption that `words_alpha.txt` is pre-deduped is now encoded only in a comment. If upstream ever introduces duplicates, `write_filtered` would silently emit duplicates. The cost is negligible (Phase 2's `letter_counts` doesn't care about word dedup — it counts letter occurrences across all words regardless), but the implicit assumption is now a supply-chain dependency on upstream's invariant. Acceptable because: (a) regen is manual, (b) the maintainer sees the counts printed, (c) constraints.md already states "Reproducible corpus" as a constraint. **Rating: benign, noted for completeness.**

### 3. Output file trailing newline — **benign**
- **Design said:** Silent.
- **Implementation chose:** `"\n".join(selected) + "\n"` — POSIX-style trailing newline.
- **Forward impact:** None; Phase 2's `load_words()` uses `.splitlines()` which handles both presence and absence equivalently. Existing `data/words.txt` also has a trailing newline so consistency is preserved.

### 4. Output files are sorted alphabetically — **notable**
- **Design said:** Silent on ordering.
- **Implementation chose:** `sorted(...)` output — alphabetical ascending.
- **Forward impact:** Matters for two forward consumers: (i) Phase 2's `letter_counts` / `bigram_counts` etc. are order-independent so no computation risk; (ii) DR4 / Phase 4's reference tables will be sorted by frequency or column — order-independent too. **But** if `top_n_by_score` uses Python's stable `sorted()` with descending-by-score, the secondary key will end up alphabetical "for free" because the input order is alphabetical. That's exactly what AC4.1 mandates ("alphabetical tie-break"). Phase 3 test must not accidentally rely on this — it should explicitly test tie-break rather than relying on input ordering. Already spelled out in Phase 3's test list ("Tie-break: two words with equal scores returned in alphabetical order"), so no defect, but worth noting: the Phase 1 decision to pre-sort subtly couples to Phase 3's tie-break implementation. If someone ever regenerates the corpora in a different order (e.g., shuffled for testing), tie-break correctness still needs to hold via explicit `sorted` with an alphabetical secondary key.

### 5. Upstream URL pinned to `master` branch (not a commit SHA) — **notable**
- **Design said:** "dwyl/english-words (~370k English words) used as the raw corpus source" — silent on pinning.
- **Implementation chose:** `https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt`.
- **Forward impact:** constraints.md specifies "Reproducible corpus: Re-running `scripts/build_corpora.py` against the *same upstream commit of dwyl/english-words* produces byte-identical `words_10.txt` and `words_3_to_10.txt`". Pinning to `master` means re-running tomorrow can legitimately produce different outputs if upstream merges a PR — and there is no recorded way to detect that except by diffing the committed files. This is not a defect in Phase 1 (the constraint is on the *script*, which is deterministic given fixed input), but the reproducibility guarantee only holds by implicit trust in upstream's master not moving. If the maintainer ever needs to regenerate "the same" corpus years later, the `master` pin is unhelpful. **Recommendation for Phase 7 documentation update:** note this caveat in `scripts/build_corpora.py` header or CLAUDE.md — perhaps a SOURCE_REF constant with a hash of the fetched file, logged at write time. Flagged as Medium — does not need to be addressed in Phase 1 but should be surfaced before the constraint is formally claimed to hold.

### 6. Script uses REPO_ROOT relative to `__file__` — **benign**
- **Design said:** Silent on invocation assumptions.
- **Implementation chose:** `REPO_ROOT = Path(__file__).parent.parent`. Works from any CWD.
- **Forward impact:** Makes the script robust to invocation from inside or outside the repo. Good.

### 7. Empty `scripts/__init__.py` — **benign**
- **Design said:** Explicitly specified in Task 1.
- **Implementation chose:** Followed spec.
- **Forward impact:** None. Package marker; not strictly needed on Python 3.14+ with namespace packages, but harmless and consistent with the design's phrasing.

### 8. Removed `docs/data/` empty directory — **benign**
- **Design said:** Phase file Task 2 explicitly `rmdir docs/data` after move.
- **Implementation chose:** Followed spec. `docs/data/` no longer exists; `docs/five/data/` does.
- **Forward impact:** None.

### 9. `docs/ten/index.md` placeholder wording — **benign**
- **Design said:** "`docs/ten/index.md` — empty placeholder."
- **Implementation chose:** Minimal placeholder with `"*(Generated by main_ten.py — placeholder, content arrives in Phase 6.)*"`.
- **Forward impact:** None. Phase 6 will overwrite this file. The choice of explanatory text over literally empty is friendlier to anyone previewing the site mid-implementation.

### 10. Landing page "Source" section + TODO comment — **notable**
- **Design said:** Phase file Task 3 specified the exact markdown.
- **Implementation chose:** Followed it verbatim, including `<!-- TODO: confirm the canonical GitHub URL for this repo and add a "Code:" link here. -->`.
- **Forward impact:** A TODO is now shipped in published content. It is an HTML comment (invisible to readers, visible to source-view), so the user-facing impact is zero, but it's a latent maintenance item. **Recommendation:** track this explicitly — either resolve it in Phase 7 alongside the freshness update, or move it to an issue. Otherwise it will live forever. Flagged as Low.

### 11. `main.py` module docstring not updated — **notable**
- **Design said:** Phase file Task 2 only specified the three path constants.
- **Implementation chose:** Literally just those three constants. The existing docstring on line 1 still reads `"""Compute letter frequencies from five-letter English words and generate docs/index.md."""` — now wrong (output is `docs/five/index.md`).
- **Forward impact:** Documentation drift within `main.py`. Minor. A reader seeing the docstring plus the constants will detect the mismatch, but automation won't. **Recommendation:** add to Phase 7 doc refresh. Flagged as Low.

## Forward Fitness

This phase's structural readiness for the downstream phases (2–7) — focusing on whether what was built has the right *shape* for what's coming.

### Phase 2 (reference frequency module) — ready

Phase 2 needs `list[str]` inputs to `letter_counts`, `bigram_counts`, etc. The committed `data/words_3_to_10.txt` is flat newline-delimited lowercase a–z; `Path.read_text().splitlines()` (the existing `main.py` pattern on line 20) produces exactly `list[str]` with the right shape. No issue.

- **AC1.4** ("every letter a–z has non-zero counts on the actual `words_3_to_10.txt`"): 248,010 words with every starting letter present (checked first letters `a`..`z` by a sampling). Structurally satisfied.
- **AC10.4** ("'s' present in first-letter and 'e' present as last-letter"): spot check — corpus contains words starting with 's' and ending with 'e'; structurally satisfied.

### Phase 3 (scoring module) — ready

Needs rate dicts produced by Phase 2. No Phase-1 artifact touches scoring. Corpus supports the precondition that rate dicts will be non-zero-sum.

### Phase 4 (reference-table rendering) — ready

Needs a CSS file to append to; `docs/css/heatmap.css` moved under `docs/five/` — **WAIT, is it there?** Let me double-check:

Checked: `docs/css/` still exists at top-level (`ls /home/brian/llm/letterfreq/.worktrees/ten-letter-page/docs/` shows `css/`, `five/`, `js/`, `ten/`, `data/` — wait, `data/` too?).

Actually: `ls docs/data` returned "No such file or directory", which is correct. `ls docs/` shows `css/`, `js/`, `ten/`, `five/`, `index.md` — the list output above was visually ambiguous but after cross-checking, `docs/css/` is top-level and will serve `/five/` and `/ten/` equally through `zensical.toml` `extra_css = ["css/heatmap.css"]`. Good.

**However, this is a baked-in assumption worth noting:** `docs/css/heatmap.css` was **not** moved under `docs/five/` in Task 2. The design plan Phase 4 says "append rules for a generic two-column 'side-by-side reference pair' layout" — both pages will share `heatmap.css`. This is fine because:
- `zensical.toml`'s `extra_css = ["css/heatmap.css"]` is a site-wide include.
- Phase 4's `.ref-pair` class only applies when the `/ten/` page uses it; `/five/` pages won't accidentally pick it up.

This is a **structural choice the implementation made** — single shared CSS file — that's consistent with the design's "reused as-is" language in the Existing Patterns section. Correct call, no finding.

### Phase 5 (ranking-table rendering) — ready
Depends on Phase 3 output. No Phase-1 artifact relevant.

### Phase 6 (main_ten.py orchestration) — ready

Needs:
- `data/words_10.txt` — present, 45,872 lines, shape valid.
- `data/words_3_to_10.txt` — present, 248,010 lines, shape valid.
- `docs/ten/index.md` destination — present (placeholder, will be overwritten).

The `main.py` pattern of `INDEX_MD.write_text(page)` at line 458 is the pattern Phase 6's `main_ten.py` will mirror. The path constants are in the expected place.

### Phase 7 (doc update + corpus invariant tests) — ready

Needs:
- `data/*.txt` files to test — present.
- `CLAUDE.md` to update — at repo root (worktree's CLAUDE.md is a stale copy from the initial commit — it still says `zensical 0.0.28`, references `docs/index.md` and `docs/data/`, no `docs/five/`, no `docs/ten/`, no `letterfreq/`, no new corpora). **This is expected** — Phase 7's explicit job is to bring CLAUDE.md current.

**Hostile-reviewer angle:**
A hostile reviewer looking at Phase 1 against later human UAT would probe:
- _"What if upstream `master` moves between when the corpora were committed and when the maintainer regenerates?"_ — covered under Baked-in #5.
- _"What if the built `/five/` drill-downs silently break because the JSON pathing was assumed?"_ — AC7.2 is tagged for manual visual inspection only. The bare-relative `fetch()` pattern was preserved, JSON files are co-located; I verified both. But there's no automated regression check. **Flagged as Medium** (candidate fitness function): a 5-line test that imports `docs/js/sort-tables.js` text and asserts `fetch("data/bigrams.json")` is present alongside existence of `docs/five/data/bigrams.json`. Not required for Phase 1 gate, but worth considering for Phase 7.
- _"Does the phase actually build with `--clean`?"_ — yes, verified at 0.30s.
- _"What if `words_10.txt` contains a 10-letter substring of a longer invalid upstream line that passed the lowercase filter?"_ — Not possible given the filter logic: `ALPHA_LOWER = re.compile(r"^[a-z]+$")` then `length == 10` selection. Confirmed invariant.
- _"Is there a regression test that `data/words.txt` wasn't accidentally touched?"_ — No. A one-line git-status assertion in Phase 7's `test_corpora.py` would guard this structurally (AC8.3 is already scheduled there, implicitly).

## Situated Accountability

This is a corpus/infrastructure phase with one non-trivial domain-encoding choice: **which words are admissible input**. The filter `ALPHA_LOWER = re.compile(r"^[a-z]+$")` encodes a particular perspective on what counts as "an English word."

**Whose perspective shaped this?**
- The maintainer, operating in a specific tradition: letter-frequency analysis of lowercased, ASCII-only, alphabetic-only English. This is consistent with the existing `data/words.txt`'s shape (also `[a-z]{5}`).
- The dwyl/english-words corpus itself — a community-maintained list that already filters out most non-English entries, but contains many archaic, technical, and rare words (e.g. `abannition`, `abaptiston` visible in the first 10 lines of `words_10.txt`).
- No persona consultation is recorded for this choice; personae.md lists Maintainer and Site visitor only.

**Who bears costs not visible in the code?**
- Users of English dialects that routinely use loanwords with diacritics (naïve, résumé, café) — excluded at the filter. Observably rare in 10-letter form but present in 3–10 letter range (notable for word-game contexts).
- Contractions and possessives (`don't`, `can't`, `someone's`) — excluded because apostrophes fail the filter. Fine for frequency analysis because they would distort bigram counts with rare apostrophe-adjacent pairs; the design's silence on this is actually a reasonable default.
- Proper nouns — partially included (`abyssinian`, `ashkenazic` visible in the corpus head). The corpus does not systematically distinguish them. For a "common English letters/bigrams/trigrams" view, this inflates some letter counts (e.g. capitals at start of proper nouns get lowercased and counted the same as common nouns).
- Highly archaic / technical terms — the `words_10.txt` head shows `abaptiston`, `abaptistum`, `abecedaire`, `aberdavine`. These contribute equal weight to 10-letter word scoring as common English words (`aardwolves`, `abandoners`). The "top-50 ten-letter words by letter coverage" will score on a corpus where common and archaic words are treated equally. **This is a baked-in assumption inherited from the upstream corpus** — not introduced by Phase 1, but materialised by committing the filtered files.

**What's absent?**
- Frequency-of-use weighting. "English letter frequencies" as framed by the landing page implies common usage; the corpus treats all words as equally-weighted types, not tokens. A corpus weighted by actual usage frequency (Google N-gram, SUBTLEX) would produce noticeably different letter rates. The design plan does not flag this distinction. **Forward-phase readers will infer "common English" from the site; they are actually seeing "uniformly-weighted dictionary English."** This is a notable situated-knowledge point worth capturing explicitly in the glossary and/or landing page — the term "baseline corpus" in `glossary.md` describes the derivation but not the consequent semantic ("type frequency, not token frequency").
- Punctuation-containing entries (hyphenated compounds) — excluded by filter. For 10-letter analysis this excludes e.g. hyphenated adjectives; minor.
- Non-English script — out of scope and filtered. Obvious.

**Recommendation (Medium):** Add one sentence to the landing page or the glossary entry for "baseline corpus" noting: _"Per-word (type) counts from the dwyl/english-words dictionary. Does not reflect real-world usage frequency (token counts would differ, e.g. 'the' would dominate)."_ This is a small but important honesty about what the numbers mean. Does not need to block Phase 1 — can be folded into Phase 6's landing-page finalisation or Phase 7's doc refresh.

## Architecture Doc Updates

`dev_docs/architecture/` exists and was already written with foresight of the ten-letter work (glossary, constraints, personae, DFDs all reference the forthcoming `letterfreq/` package, `main_ten.py`, new corpora, DR8 positional endpoint scoring, `/five/` and `/ten/` routes). This phase landed the first slice of what the docs already anticipated. Review whether the docs now need updates:

| Doc | Current state | Phase-1 impact | Update needed? |
|-----|--------------|----------------|----------------|
| `glossary.md` | Describes baseline corpus, trigrams, positional endpoint score, transparency column, FCIS. All correct. | No new terms introduced. | **None.** Already anticipates the work. (Optional: add "type frequency vs token frequency" disambiguation — see Situated Accountability.) |
| `constraints.md` | Capacity row names `words_10.txt` and `words_3_to_10.txt` with current counts "TBD". | Can now fill in counts: 45,872 and 248,010. | **Minor update recommended** — replace "TBD" with actual counts. Flag: Medium. Best folded into Phase 7 doc refresh. |
| `personae.md` | Describes Maintainer key scenario #2: "Updating the upstream corpus: run `scripts/build_corpora.py` → review diffs → re-run all `main*.py` scripts → commit." | Scenario now actually works. | **None** — written correctly in anticipation. |
| `dfd/0-context-diagram.md` | Generic. | No change. | None. |
| `dfd/1-corpus-generation.md` | Describes the three files as "Committed; produced one-shot" with `scripts/build_corpora.py` as the producer. Uses phrase "prospective" for the new files. | Files now exist. | **Minor update recommended** — replace "prospective" language with "as of 08fc730" or similar. Flag: Low. Phase 7 candidate. |
| `dfd/2-frequency-analysis.md` | Describes post–design-plan layout: `main.py` writes to `docs/five/`, `main_ten.py` forthcoming, `letterfreq/` package forthcoming. | `main.py` now writes to `docs/five/`. | **Minor update recommended** — the phrase "After the design plan it writes to `docs/five/index.md`" should become "writes to `docs/five/index.md`" (present tense, no conditional). Flag: Low. |
| `dfd/3-site-build-serve.md` | Describes multi-page layout as "post–design-plan". | Now real. | **Minor update recommended** — as above, drop the "post–design-plan" caveat. Flag: Low. |

**No new architecture docs required.** The original architecture-maintenance session (commit `fab58bf`) bootstrapped docs with the ten-letter work in mind, so Phase 1's work is already reflected in intent. Only tense/freshness fixes needed, best grouped into the Phase 7 doc-refresh commit.

## Findings Summary

### High (count: 0)

_No high-severity coherence findings._ The phase cohered with the design on every structural dimension I could verify. The only "near-high" item is the lack of an automated regression guard for the drill-down `fetch()` path resolution, but the phase file explicitly declared that AC7.2 would be verified by manual visual inspection — the absence is declared, not hidden.

### Medium (count: 4)

1. **Upstream corpus not pinned by commit SHA.** `scripts/build_corpora.py` uses `master`. `constraints.md` claims "Re-running against the same upstream commit produces byte-identical outputs" — that constraint is not enforceable given `master`-pinning. Recommend either (a) pinning to a commit SHA, (b) recording the upstream commit at write time (e.g. fetch `https://api.github.com/repos/dwyl/english-words/commits/master` and capture SHA into a sidecar file), or (c) softening the constraint wording in `constraints.md` to acknowledge upstream can move. Best addressed during Phase 7's doc refresh.

2. **Candidate fitness function for AC7.2 — JS `fetch()` path alignment.** No automated check that `docs/js/sort-tables.js`'s `fetch("data/bigrams.json")` corresponds to an actual `docs/five/data/bigrams.json` file. Add a tiny static assertion test — regex for the fetch path + `Path.exists()` check. Trivial, catches the highest-risk regression path (re-ordering phases or future moves silently breaking `/five/`). Candidate for Phase 7's `tests/`.

3. **Type-vs-token frequency framing absent from user-facing content.** The landing page and glossary don't distinguish dictionary-based letter frequencies (what this project computes) from usage-weighted letter frequencies (what most readers will assume when they read "English letter frequencies"). Add one clarifying sentence to the glossary "baseline corpus" entry and/or to `docs/index.md`. Candidate for Phase 6 (landing page finalisation) or Phase 7 (doc refresh).

4. **Candidate fitness function for AC7.1 — build smoke test.** No automated assertion that `zensical build --clean` succeeds. A `subprocess.run(["uv", "run", "zensical", "build", "--clean"], check=True, timeout=60)` test in Phase 7 would guard against config drift. Low complexity, high signal.

### Low (count: 3)

1. **TODO comment shipped in `docs/index.md`.** "confirm the canonical GitHub URL" — HTML comment, user-invisible, but persistent. Resolve in Phase 7 or move to an issue.

2. **`main.py` module docstring stale.** Line 1 still references `docs/index.md` as the output; actual output is `docs/five/index.md`. Fold into Phase 7 doc refresh.

3. **Architecture docs use "prospective" / "post–design-plan" tense.** `dfd/1-corpus-generation.md` and `dfd/2-frequency-analysis.md` / `dfd/3-site-build-serve.md` describe Phase-1 outcomes as still-future. Fold into Phase 7 doc refresh. Also `constraints.md` capacity row: replace "TBD" with actual line counts (45,872 and 248,010).

## Overall Assessment

**Coheres.** Phase 1 matches the design's architectural intent and the phase file's explicit task list with no erosion and negligible drift. The baked-in assumptions are either benign (timeout, trailing newlines, package marker) or notable-but-acceptable (sorted output, upstream `master` pin — both worth surfacing to the maintainer but neither requires rework). Forward fitness is solid: Phases 2–6 will find the shapes they need, and Phase 7's doc-refresh scope already naturally absorbs the housekeeping (`main.py` docstring, architecture tense updates, constraints.md TBD counts, optional TODO resolution).

The single substantive human-decision item is the type-vs-token framing — whether to acknowledge explicitly that these are dictionary-uniform counts rather than usage-weighted counts. The maintainer should decide whether that framing goes in the landing page, the glossary, or both. It is a naming/accountability question, not a technical one.

Rollback tag `pre-ten-letter-page` confirmed present — rollback path is clean.

No blockers for proceeding to Phase 2.
