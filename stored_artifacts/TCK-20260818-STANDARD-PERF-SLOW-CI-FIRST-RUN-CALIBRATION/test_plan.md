---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION
artifact_type: test_plan
tags: [testing, bug, performance, calibration]
---

# Test Plan — TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION

## Normal flow
- Each edited test's own node, run individually under
  `pytest <nodeid> -m "slow or extra_slow" --resource-budget large -v -s --tb=long` (the real CI
  `slow` job's own invocation pattern), must PASS with real (not mocked) numbers.

## Edge cases / regression-prone paths
- `test_api_snapshot_performance_stress[5000]`: verify the OTHER two `_run_snapshot_benchmark`
  callers in the same file (`test_api_snapshot_performance_comparison[100]`/`[1000]`, which share
  the helper function I edited) still pass unmodified — the warmup addition is scoped to the
  to_readonly section only, must not change deepcopy/present_minimal/present_full behavior.
- `test_perf_passive_scaling`: verify `[100]`/`[1000]` (the two non-5000 parametrizations, whose
  own thresholds are untouched) still pass — confirms the `allowed_delta` branch change is scoped
  correctly to `count>=5000` only.
- `test_perf_strategic`: verify `[100]` (untouched real value, well under both old and new
  threshold) still passes alongside the fixed `[500]`/`[1000]`.
- Re-run `test_perf_strategic[1000]` after observing one transient failure under heavy concurrent
  system load (shared dev box, load average 5+, near-exhausted swap) — confirmed PASS in isolation,
  documented as environmental noise, not a fix regression.

## Failure modes
- Confirm none of the 4 edited files still import `os` if its only use (`os.environ.get("CI")`)
  was removed — avoid a dangling unused import.
- Confirm the fast lanes are unaffected: `pytest tests/arena tests/perf -m "not slow and not
  extra_slow" --collect-only -q` before/after — no test newly collected or dropped from fast lanes
  (all 5 edited tests already carry `@pytest.mark.slow`, only the `skipif` internals changed).

## Architecture checks
- No `src/` files modified — pure test-threshold/test-methodology changes, so the "authoritative
  application path" / "durable state" / "read-only logic didn't mutate live state" checks don't
  apply to this ticket's diff.
- Confirm `tests/certification/test_cert_long_run_stability.py` and
  `tests/integration/world/test_long_run_stability.py` remain byte-identical (git diff empty) —
  explicitly out of scope, owned by the sibling determinism-investigation agent.

## Full local verification command (final gate before closing)
```
pytest tests/arena/test_arena_stress.py tests/perf/test_hard_law_monitor_overhead.py \
  tests/perf/test_perf_api_snapshot.py tests/perf/test_perf_passive_scaling.py \
  tests/perf/test_perf_strategic.py -m "slow or extra_slow" --resource-budget large --tb=short -q
```
