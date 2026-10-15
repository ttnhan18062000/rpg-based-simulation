---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, benchmarking, regression]
---

# `docs/observability/baselines/`

One file is read from here: **`latest.json`**, by `python3 -m src gate` and `python3 -m src compare-sweep --baseline` (`docs/guides/simulation.md`, `docs/guides/observability.md`).

`latest.json` is a `BaselineConfig` (`baseline_v1`) written by `python3 -m src generate-baseline <sweep_id>` from a real sweep of the `idle` sandbox scenario (seeds 1 to 5, 50 ticks, `LIGHT`), carrying the current `cost_accounting_version` (`DEV-017`). It was created by `TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS`; the sweep ran on one loaded development host, so it is evidence about that host that day, not a capacity claim, and the sweep gate blocks nothing (OD-8).

To replace it: run a sweep with the same config, `python3 -m src generate-baseline <sweep_id>`, copy `data/run_sets/<sweep_id>/baseline.json` here, and check that `compare-sweep` and `gate` of a second identical sweep both give a tick-cost verdict (PASS, FAIL or INCONCLUSIVE with its reason) and not a validation error.

The 14 per-profile files and `matrix_full.json` that used to sit here (captured 2026-05-19, before the DEV-017 tick-cost correction, with no consumer) were deleted by the same ticket; they are in git history. The performance baselines proper (schema 1.1 records) live in `tests/perf/baselines/` and are written only by `tools/perf/baseline_lifecycle.py promote`; `docs/performance/baseline_invalidation_ledger.md` says which are re-recorded and which are pending.
