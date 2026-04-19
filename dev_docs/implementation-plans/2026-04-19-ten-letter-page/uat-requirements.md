# UAT Requirements — Ten-Letter Page

Human-judgment falsification entries. Each requires a human to USE the built thing
and exercise judgment that automated tests cannot capture.

Quality gate: every entry must have (1) what the human DOES (an action, not inspection),
(2) what they're JUDGING (subjective quality), (3) what FAILURE looks like (concrete experience).

Most of this project's ACs are automatable (counts, regex shapes, structural HTML
strings). The remaining items below need a human in front of a browser because the
project has no headless-browser test harness — adding one is out of scope for this
implementation cycle.

---

## Phase 1: Site restructuring + Zensical bump

### AC7.1 + AC7.4 — Build succeeds and navigation is correctly exposed

**This decision assumes:** A zensical 0.0.33 build with the explicit `nav` block in `zensical.toml` produces a site where Home, Five-letter, and Ten-letter are reachable from every page.

**To shatter it:** Run `uv run zensical serve`, open http://localhost:8000, and click Home → Five-letter → Ten-letter from the sidebar / nav drawer (whatever Zensical 0.0.33 renders by default). Then click back through the same path in reverse.

**It's wrong if:** Any of the three pages is missing from the visible navigation, the nav order is something other than Home / Five-letter / Ten-letter, or a click takes you to a 404.

### AC7.5 — Dark/light toggle and instant navigation still work after the bump

**This decision assumes:** Zensical 0.0.33 preserves the dark/light palette toggle behaviour and `navigation.instant` prefetching that 0.0.28 had. The changelog reports no breaking changes for these features, but only a human exercising the UI can confirm.

**To shatter it:** With the dev server running, click the dark/light toggle on each of the three pages and confirm the colour scheme actually changes. Then click between pages and watch for full-page reload flicker (URL bar updates without flicker means `navigation.instant` is working).

**It's wrong if:** The toggle is missing, doesn't switch schemes, or the page flickers as if doing a full reload on every nav click.

---

## Phase 1 + Phase 6: Five-letter page interactions still work after the move

### AC7.2 — Bigram and trigram drill-downs on /five/ still resolve their JSON correctly

**This decision assumes:** Moving `docs/data/{bigrams,trigrams}.json` to `docs/five/data/` allows the bare-relative `fetch("data/bigrams.json")` calls in `sort-tables.js:39` and `trigram-expand.js:8` to keep working from `/five/index.html`. We argued this in the design plan but it has to be tried in a browser.

**To shatter it:** On `/five/`, click any non-zero bigram cell. Confirm a drill-down panel appears below the grid showing the neighbour-letter distribution bars. Then click any non-zero trigram cell and confirm a completion list appears.

**It's wrong if:** The drill-down panel doesn't appear, appears empty, or the browser console shows a 404 for `/five/data/bigrams.json` or `/five/data/trigrams.json`.

---

## Phase 4 + Phase 5 + Phase 6: Ten-letter page tables look right

### AC5.3 + AC5.5 — Side-by-side reference pairs are responsive

**This decision assumes:** The new `.ref-pair` CSS rule (`grid-template-columns: 1fr 1fr` collapsing to `1fr` below 720px) reads cleanly at desktop and mobile widths.

**To shatter it:** On `/ten/`, view both the start/end trigram pair and the first/last letter pair at desktop width (>720px). Confirm the two tables are side-by-side. Then resize the browser to <720px width (or use device-emulation devtools) and confirm both pairs stack vertically with reasonable spacing.

**It's wrong if:** The two halves of either pair are not side-by-side at desktop width, overlap, overflow horizontally, or refuse to stack at narrow widths.

### AC5.4 + AC6.4 — Click-to-sort works on the new tables

**This decision assumes:** Using the existing `sortable-table` and `sortable` CSS classes (per `sort-tables.js`) gives the new ten-letter tables the same click-to-sort behaviour as the five-letter tables, with no per-page JS changes.

**To shatter it:** On `/ten/`, click the "Count" column header in the letter-frequency table. Confirm the table re-orders and a sort-direction indicator (arrow / class) appears on the header. Click again to reverse. Repeat on the bigram top-100 table, on each side of both side-by-side pairs, and on each of the four ranking tables (sort by Score, then by another column).

**It's wrong if:** Any column header is non-clickable, clicking a header doesn't change row order, or the visible sort-direction indicator doesn't match the row order.

*(AC6.5 doubled-endpoint behaviour is fully covered by the automated `test_positional_ranking_doubled_endpoint_word` test in Phase 5 — no UAT entry needed. The earlier UAT draft asked the human to find a same-first-last word in the corpus, which may not exist in the top-50; the automated test on a synthetic `aaaaaaaaaa` word catches the bug deterministically.)*

---

*(AC9.1 + AC9.2 are now covered by automated tests — see `tests/test_documentation.py` added in Phase 7 Task 1B per peer-review finding H6. No UAT entry needed.)*
