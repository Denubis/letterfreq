# Dependency Rationale

Falsifiable justifications for every direct dependency. Each entry records why the package was added, what evidence supports its use, and who it serves.

Maintained by design plans (when adding deps) and controlled-dependency-upgrade (when auditing).

## zensical
**Added:** 2026-03-22
**Design plan:** docs/design-plans/2026-03-22-five-letter-freq-site.md
**Claim:** Zensical generates the static site from Markdown sources in `docs/` and is invoked via `zensical build` in CI and local development.
**Evidence:** `zensical.toml` (configuration), `.github/workflows/docs.yml` (build step), `docs/index.md` (source content)
**Serves:** Build pipeline, deployed site

## polars
**Added:** 2026-03-22
**Design plan:** docs/design-plans/2026-03-22-five-letter-freq-site.md
**Claim:** Polars computes cross-tabulation and matrix operations for bigram/trigram frequency data in `main.py`, replacing verbose nested-loop counting with DataFrame operations.
**Evidence:** `main.py` (imports and uses polars for frequency computation)
**Serves:** Build pipeline (data generation step only, not runtime)
