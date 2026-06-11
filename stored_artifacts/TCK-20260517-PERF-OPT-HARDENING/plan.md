---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260517-PERF-OPT-HARDENING
artifact_type: plan
tags: [perf, opt, hardening]
---

# Implementation Plan: Performance Optimization Hardening

## Milestone 1: Fix `force_full_scan` as a real reference path
- Create `get_relevant_entity_ids(state, update, domain)` helper in `src/core/dirty.py`.
- Update `InteractionPhase.resolve`, `StrategicRedirectionSystem.resolve`, `update_groups`, `shop.py`, `CapacityEnforcementPhase.resolve`, and `TownResolutionSystem.resolve` to use the helper.
- Verify `test_dirty_set_vs_full_scan_parity` passes flawlessly.

## Milestone 2: Move runtime budget enforcement after final tick cost
- In `src/engine/kernel.py`, move the budget enforcement check (`self._state.tick > 5 and self._final_compute_ms > min(hard_cap, limit_ms)`) to after `self._final_compute_ms = sum(self._phase_costs.values())`.

## Milestone 3: Remove hot-path `print()` calls
- Replace hot-path prints in `intelligence.py`, `pipeline.py`, `tactical.py`, and `inventory.py` with `logger.debug`.

## Milestone 4: Split API snapshot performance tests
- Split `test_perf_api_snapshot.py` into `test_api_snapshot_performance_comparison` (100, 1000) and `test_api_snapshot_performance_comparison_slow` (5000, `@pytest.mark.slow`).

## Milestone 5: Add real assertions to passive scaling
- Add explicit p95 latency thresholds in `test_perf_passive_scaling.py` (50ms for 100, 200ms for 1000, 800ms for 5000).

## Milestone 6: Register pytest markers
- Add `integration` and `e2e` to `pyproject.toml` under `[tool.pytest.ini_options] markers`.

## Milestone 7: Make baseline regression strict in CI
- Update `test_perf_regression_baseline.py` to check `tests/perf/baselines/*.json` and fail if missing in CI mode.

## Milestone 8: Re-run optimization proof matrix
- Execute full unit and performance verification suites to ensure 100% correctness and zero regressions.
