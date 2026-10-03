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
The seven findings for perf-planner are in the deliverable, section 1. Main points: one producer (`BenchHarness`) feeds most files; no format has a schema version, content version, DET-PORT tier or gate tier; three percentile algorithms; two threshold policies; `optimization_proof` states conclusions as fixed text; no `INCONCLUSIVE` exists.

## Limits
`pytest-benchmark`'s `machine_info` keys and the exact `pyperf` release were not confirmed from the fetched pages (docs fetch was rate-limited once). Both are listed as open questions in the deliverable.
