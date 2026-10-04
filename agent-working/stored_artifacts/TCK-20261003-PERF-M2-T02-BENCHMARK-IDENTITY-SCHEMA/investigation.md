---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
date: 2026-10-03
tags: [performance, documentation]
---

# Investigation: TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA

## Method
A read-only subagent inventoried 25 result formats from code (no benchmark, baseline, profile or pytest run). I then re-checked the claims the schema leans on: none of the 15 `tests/perf/baselines/*.json` contains `mode_sequence`; `_RUNTIME_MODE_HARD_SCENARIOS` is an empty frozenset; `perf_baselines.json` has `entries: {}`; `PerfRegressionGate` is imported only by its own unit test (plus two tools/tests that cite it in text); `_calculate_stats` uses `sorted[int(n*q)]`. Tool output formats came from the `pytest-benchmark` 5.3.0 source and the `pyperf` stable docs.

## Findings
The seven findings for perf-planner are in the deliverable, section 1. Main points: one producer (`BenchHarness`) feeds most files; no format has a schema version, content version, DET-PORT tier or gate tier; three percentile algorithms; two threshold policies; `optimization_proof` states conclusions as fixed text; no performance result format or perf gate has an `INCONCLUSIVE` outcome.

## Limits
`pytest-benchmark`'s `machine_info` keys and the exact `pyperf` release were not confirmed from the fetched pages (docs fetch was rate-limited once). Both are listed as open questions in the deliverable.

## Review follow-up (2026-10-03)
perf-planner's spot-checks found two errors in the subagent's findings (the percentile boundary and an over-broad INCONCLUSIVE claim). All seven findings in the deliverable's section 1 were then re-verified against code by the implementer: the proof generator's 1.0 defaults and unchecked baseline profile, the single `make_perf_profile` factory hard-coding `CLASS_A`, the absent length check in `check_perf_regression.py`, the percentile index arithmetic (n = 20, 50, 100), the two threshold policies, the `latest.json` writers (two, not three), and the `INCONCLUSIVE` uses. Corrected: percentile boundary, INCONCLUSIVE scope, `latest.json` writer count.
