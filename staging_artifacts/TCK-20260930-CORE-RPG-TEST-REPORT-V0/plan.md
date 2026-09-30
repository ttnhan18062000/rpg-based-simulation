---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-TEST-REPORT-V0
artifact_type: plan
tags: [testing]
---

# Plan: core-RPG test report v0

One module, `tools/test_architecture/core_rpg_report.py`, pure functions per layer plus a `build_report(inputs)`
that returns a plain dict, and a `render_markdown(report)`. Determinism: sorted keys, no wall clock (`as_of`
and `sha` are inputs), no absolute paths in the output (repo-relative), stable ordering everywhere.

Layers (each: value + denominator, or a state):
1. inventory/classification: AST scan of `tests/**/test_*.py`. Signals: directory rule and import rule
   (from the overview's §10 definitions). Class: `both` -> `classified`, disagreement -> `uncertain`, neither -> `not-core-rpg`.
2. lanes: parse `.github/workflows/test.yml` pytest steps (paths, marker filter, `--junit-xml`, whether the job uploads it).
   Per file: fast-lane coverage or `no-lane`.
3. execution: from supplied JUnit files. Per core-RPG test file: outcome counts, `not-run` (JUnit supplied, file absent),
   or `no-junit-artifact` (no JUnit supplied at all). Separate inputs keep their own run ids.
4. coverage: supplied `coverage json` -> per `src/<package>` line % (+branch if present), `provisional-local`; else `no-coverage-artifact`. Domain coverage `not-derived`.
5. parity: read-only counts by status from `docs/parity_ledger/*.yaml` with denominator.
6. SimQ `skipped-no-data`, census `unstable`: fixed read-only states with the reason.
7. mutation: `tests/mutation/baselines/*.json` -> `fresh`/`stale` (target sha256 vs current, or older than `stale_after.days` at `as_of`).
8. escaped defects: tickets tagged `escaped-defect`, per month from the tag's registration month to `as_of`'s month; 0 is real; `tag-not-registered` if absent.
9. manifest + limits.

CLI: `--sha`, `--as-of`, `--junit PATH...`, `--coverage PATH`, `--out-dir`. Exit 0 always for a produced report.
