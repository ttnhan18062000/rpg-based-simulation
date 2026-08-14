---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE
artifact_type: test_plan
tags: [observability, performance, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE

## Regression Surface

The 3 existing tests in `tests/perf/test_simq_isolation_overhead.py` must continue passing
unmodified — this ticket only adds new helpers/tests, never touches the existing 3.

## New Tests Required

- `test_push_shaper_registry_overhead_benchmark` (`@pytest.mark.slow`) — produces
  `cpu_time_total_delta_s` for `ENABLE_PUSH_EVENT_SHAPERS=ON` vs `OFF` under `inprocess` mode,
  asserts both deltas are positive (sanity check, mirrors the existing 3-mode benchmark test's own
  assertion shape).
- `test_push_shaper_registry_overhead_within_regression_band` (`@pytest.mark.slow`) — the actual
  standing gate: asserts overhead stays under the locked 25% band.

## Scoped Pytest Commands

```
pytest tests/perf/test_simq_isolation_overhead.py -m slow -s -q
```

## Anti-Drift Test Guards

- Both new tests reuse `ModeResult`/`_clear_quality_env`/`BenchHarness`/`PROD_SMALL` — no
  duplicated measurement logic that could drift from the existing 3 tests' own conventions.
- Threshold (25%) is locked from 2 real measured runs on this session's hardware (documented in
  `docs/performance/simq_isolation_overhead.md`'s new section), not guessed — matching the
  existing file's own convergence-check discipline (run twice, confirm divergence is within 10%,
  commit the second run).

## Results (this session)

- Run 1: `shapers_off` `cpu_time_total_delta_s=5.870s`, `shapers_on=5.650s` → overhead -3.75%.
- Run 2: `shapers_off=5.970s`, `shapers_on=5.830s` → overhead -2.35%. Convergence:
  `|5.970-5.870|/5.870 = 1.7%`, well within the existing 10% convergence threshold.
- `test_push_shaper_registry_overhead_within_regression_band` run independently: -2.37% (band 25%)
  — passes with wide margin.
