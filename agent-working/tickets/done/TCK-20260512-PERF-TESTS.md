---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260512-PERF-TESTS
phase: done
date: 2026-05-12
tags: [perf, tests]
---

# TCK-20260512-PERF-TESTS

## Title
Implement performance regression tests and conftest utilities

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Establish a suite of performance regression tests using `pytest` and the enhanced `BenchHarness`.

## Scope
- [x] Create `tests/perf/conftest.py` with performance-specific fixtures.
- [x] Create `tests/perf/test_perf_idle.py`: Baseline idle performance test.
- [x] Create `tests/perf/test_perf_stress.py`: Stress test with many entities and mixed work.
- [x] Implement automated reporting (saving results to `reports/perf/`).

## Out of Scope
- Optimizing specific engine bottlenecks discovered during tests.

## Acceptance Criteria
- Tests are marked with `@pytest.mark.perf`.
- Tests use the `BenchHarness` to collect metrics.
- Tests assert that `avg_tps` and `max_rss_mb` stay within reasonable bounds (e.g., > 50 TPS for 100 entities).
- Reports are generated in JSON format.

## Related Tickets
- TCK-20260512-PERF-INVESTIGATION (Done)
- TCK-20260512-PERF-PROFILES (Done)
- TCK-20260512-PERF-SCENARIOS (Done)
- TCK-20260512-PERF-HARNESS-ENHANCEMENT (Done)

## Related Docs
- [performance_implementation.md](file:///home/vboxuser/Work/rpg-based-simulation/performance_implementation.md)

## Related Code Areas
- `tests/perf/`
- `src/perf/`

## Implementation Notes
- Use `pytest.mark.perf` to allow running with `pytest -m perf`.
- Baseline for 100 entities: > 50 TPS, < 512MB RSS.

## Test Summary
- Run `pytest tests/perf/` and verify pass/fail.

## Files Changed
- [NEW] tests/perf/conftest.py
- [NEW] tests/perf/test_perf_idle.py
- [NEW] tests/perf/test_perf_stress.py

## Completion Summary
- N/A
