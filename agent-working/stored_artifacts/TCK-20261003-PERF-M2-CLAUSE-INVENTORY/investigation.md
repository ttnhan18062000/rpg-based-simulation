---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-M2-CLAUSE-INVENTORY
date: 2026-10-03
tags: [performance, documentation]
---

# Investigation: TCK-20261003-PERF-M2-CLAUSE-INVENTORY

Full evidence is `docs/performance/performance_clause_inventory.md`. Findings that changed the ticket's
premise:

- The planner's "12 of 53 pass `hard=True`" is not reproducible: 55 call sites, 0 literal `hard=True`, 3 pass-throughs.
- `PerfRegressionGate` has no production caller; the only live baseline comparison is soft and `slow`-marked (nightly).
- 12 of 15 committed baselines record `sample_ticks: 20`, against a documented minimum of 1000.
- Calibration steps in `perf_baseline_policy.md` §4 cite a module and a directory that do not exist.
- `optimization_invariants.md` cites `test_degraded_mode_correctness.py`, which does not exist.
- `origin/main` differs from the branch base in `.github/workflows/test.yml` and `Makefile` only (of the files read);
  CI line numbers are against `ed5001057`.
