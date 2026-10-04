---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS
date: 2026-10-04
tags: [performance, benchmarking]
---

# Plan: TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS

## Summary
Rewrite the comparison and report parts of `tools/release/generate_optimization_proof.py` so every scenario is `compared` or `not_comparable`, nothing is defaulted, and report text is computed from the data.

## Steps
1. Pure `compare_scenario()` (presence, profile, sample_ticks, warmup when both record it, missing or non-positive values) and `summarize()`.
2. Reader-side shape check by reusing `tools.perf.perf_baseline.validate_latest`; exit 1 before building any harness.
3. Markdown generated from the records; provisional notice first; audit statement from `RUN_FLAGS`, per-scenario profile and ticks, and the builder's default seed read with `inspect`.
4. `main()` exits 1 when nothing is comparable; both reports are still written.
5. New stub-only tests; update the slow report test's assertions without running it.
6. Docs: two "Fixed by" lines in the schema doc.

## Scope guards
`SCENARIO_CONFIGS` is unchanged. No `src/` edit, no real run, nothing under `reports/` committed.
