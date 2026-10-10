---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-T02B-RECORD
date: 2026-10-10
tags: [performance, benchmarking, schema, determinism]
---

# Test plan: TCK-20261010-PERF-M2-T02B-RECORD

New, under `tests/unit/perf/`:

| File | Covers |
|---|---|
| `test_benchmark_record.py` | frozen record; JSON round trip; the three blocking contract fields; `hash_scheme` enum; missing required field named; embedded-or-pointer samples; collector sentinel; detected class; `nearest_rank` (1..20 gives p95 19), bounds, float noise; run-length modes; `compare`: PASS, REGRESSION, absolute floor, configurable thresholds, missing base, MAJOR and MINOR schema, missing and different `cost_accounting_version`, ten blocking-field mismatches, percentile method, unknown against known, Python patch recorded only, commit/dirty recorded only, declared-class mismatch, hash scheme, canonical and live excursion, base left NORMAL or empty, missing metric, perf-only fields ignored, no mutation |
| `test_bench_harness_record.py` | result dict key set unchanged; record emitted and round-trips; embedded samples match the latency; capacity pointer; nearest-rank in `_calculate_stats`; a record failure never fails the benchmark |
| `test_perf_profiles_canonical.py` | T07: eight variants, differ only in contract and name, defaults stay LIVE, matrix unchanged, `select_signal_source` routing; T02b: detected class (monkeypatched, all three), no hard-coded `CLASS_A` |

Existing, re-run: `tests/perf/test_bench_harness.py`, `tests/perf/test_profiler_integrity.py`, `tests/perf/test_perf_regression_baseline.py`,
`tests/unit/perf/test_perf_regression_gate.py`, `tests/unit/engine/test_signal_contract_foundation.py`, `tests/tools/test_corpus_perf_baseline.py`,
`tests/tools/test_perf_inventories_committed_in_sync.py`; `python3 -m codebase.health check`; mypy on `src/`; the parity-ledger schema gate.

## Proof Plan

| Criterion group | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| Record shape, serialization, enums | unit | behaviour | the schema doc §3 and §4 (the contract), restated as assertions | a frozen record round-trips; an invalid enum or an orphan hash is rejected at construction | `pytest tests/unit/perf/test_benchmark_record.py` |
| `compare()` outcomes | unit | behaviour | schema doc §4 and the owner decisions OD-1, OD-3, OD-4 in the M2 epic | each blocking mismatch, missing base, MAJOR bump and missing `cost_accounting_version` is INCONCLUSIVE and names the field; excursion is REGRESSION canonical and INCONCLUSIVE live; perf-only fields cannot change the answer | same file |
| Harness emits a record; nearest-rank | unit and integration (a real 20-entity kernel run) | behaviour | `ceil(q*n)` worked by hand: p95 of 1..20 is 19 | the result dict keys are unchanged; `last_record` round-trips; samples embedded or pointed to | `pytest tests/unit/perf/test_bench_harness_record.py tests/perf/test_bench_harness.py` |
| Detected hardware class; T07 variants | unit | behaviour | `HardwareClassifier.detect_class()`; the T07 ticket's acceptance criteria | no hard-coded `CLASS_A`; variants differ only in contract and name | `pytest tests/unit/perf/test_perf_profiles_canonical.py` |
| Nothing else regressed | existing suites and gates | regression | the repository's own gates | all pass; code-health 0 new / 0 worse | `pytest tests/perf/test_profiler_integrity.py tests/perf/test_perf_regression_baseline.py tests/unit/perf tests/tools/test_corpus_perf_baseline.py tests/tools/test_perf_inventories_committed_in_sync.py`; `python3 -m codebase.health check` |

Not proven: the same pass/fail of `check_perf_regression.py` on committed data (argued from nearest-rank being never higher, not run), and any `CLASS_C` host run.
