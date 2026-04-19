# Quality Constraints

Measurable limits on system behaviour. Each constraint has a metric, a target, and a verification method.

## Performance

| Constraint | Metric | Target | Verification |
|-----------|--------|--------|-------------|
| Build time (full) | Wall-clock seconds for `uv run python main.py && uv run python main_ten.py && uv run zensical build --clean` from a clean checkout. | < 30 s on developer hardware. | `time` command; check after each major change. |
| Page weight (per page) | Compressed transfer size of any single page in `site/`. | < 1 MB. | Inspect built `site/` files; sum HTML + linked JSON. |
| Browser interactivity latency | Time from clicking a bigram/trigram cell to drill-down panel appearing. | < 200 ms after JSON fetched and cached. | Manual visual check in dev tools. |

## Availability

| Constraint | Metric | Target | Verification |
|-----------|--------|--------|-------------|
| Deployment success rate | Fraction of pushes to `main` that successfully publish via `.github/workflows/docs.yml`. | 100% on green-build pushes. | GitHub Actions run history. |

## Security

| Constraint | Requirement | Verification |
|-----------|-------------|-------------|
| No PII collected | No tracking, no analytics, no user accounts, no server-side state. | Inspect `zensical.toml` and `docs/` for any analytics or third-party tracking integration; should find none. |
| No client-side secrets | No API keys, tokens, or credentials in any client-served file. | Grep `site/` and `docs/` for likely secret patterns before publish. |
| Static-only hosting | Site must be servable by any static-file host (no server-side dependencies). | Site builds to `site/`; can be served from `python -m http.server site/` with no other moving parts. |

## Capacity

| Constraint | Metric | Current | Limit | Verification |
|-----------|--------|---------|-------|-------------|
| Corpus size (per file) | Lines in `data/*.txt`. | 15,921 (`words.txt`); TBD for `words_10.txt` and `words_3_to_10.txt`. | < 1M lines per file (no hard limit; soft target keeps Python load times reasonable). | `wc -l data/*.txt`. |
| Pages per site | Markdown sources under `docs/`. | 3 after the ten-letter design plan (landing, `/five/`, `/ten/`). | Soft cap ~10 (Zensical navigation legibility; revisit if more added). | Inspect `zensical.toml` `nav` block. |

## Build Idempotence

| Constraint | Requirement | Verification |
|-----------|-------------|-------------|
| Reproducible output | Re-running `main.py` or `main_ten.py` on unchanged inputs produces byte-identical Markdown and JSON outputs. | `git status docs/` is clean after a clean re-run. |
| Reproducible corpus | Re-running `scripts/build_corpora.py` against the same upstream commit of dwyl/english-words produces byte-identical `data/words_10.txt` and `data/words_3_to_10.txt`. | Cross-machine verification on demand. |

## Constraint History

| Date | Constraint | Change | Reason |
|------|-----------|--------|--------|
| 2026-04-19 | All | Initial bootstrap. | Bootstrapped during ten-letter page design. |
