# TCK-20260517-PERF-OPT-HARDENING

## Title
Performance Optimization Hardening and Measurement Integrity

## Status
DONE

## Request Summary
Investigate and implement the performance optimization hardening plan defined in `performance_opt_hardening.md` to fix incorrect/missing logic across recent performance hardening tasks.

## Scope
- Milestone 1: Fix `force_full_scan` as a true reference path across all pipeline phases using a robust `get_relevant_entity_ids` helper.
- Milestone 2: Move runtime budget enforcement to the very end of `Kernel.tick_once()` after final phase accounting.
- Milestone 3: Remove hot-path `print()` statements in engine, systems, and AI modules, replacing them with flag-gated logger debug calls.
- Milestone 4: Split API snapshot performance test into CI-safe and `@pytest.mark.slow` manual benchmarks.
- Milestone 5: Add real performance thresholds (compute p95, memory RSS, TPS) to passive scaling tests.
- Milestone 6: Register pytest markers (`perf`, `slow`, `integration`, `e2e`, `strategic_loop`) in `pyproject.toml`.
- Milestone 7: Make performance baseline regression strict in CI mode while keeping local flexibility.
- Milestone 8: Re-run full optimization proof matrix to verify 100% correctness and performance integrity.

## Out of Scope
- Architectural changes to combat or non-performance systems.
- Re-architecting core dataclass models.

## Acceptance Criteria
- `force_full_scan` correctly overrides DirtySet narrowing in interaction, redirection, groups, shop, capacity, and town phases.
- Budget enforcement checks total tick compute latency including persistence.
- Zero hot-path `print()` calls in engine/system code during standard execution.
- CI performance tests run quickly and reliably without timing out on 5,000 deepcopy samples.
- Pytest runs without unknown marker warnings.
- 100% pass rate across unit and performance test suites.

## Related Tickets
- None

## Related Docs
- `performance_opt_hardening.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260517-PERF-OPT-HARDENING/`

## Related Code Areas
- `src/core/dirty.py`
- `src/engine/kernel.py`
- `src/engine/pipeline.py`
- `src/engine/pipeline_phases/`
- `src/engine/shop.py`
- `src/engine/tactical.py`
- `src/engine/town_resolution.py`
- `src/systems/`
- `tests/perf/`
- `pyproject.toml`

## Assumptions / Open Questions
- None

## Implementation Notes
- Fixed `force_full_scan` handling across `interactions.py`, `redirection.py`, `groups.py`, `shop.py`, `capacity_enforcement.py`, and `town_resolution.py`.
- Moved budget limit check to line 226 in `kernel.py`.
- Replaced hot-path `print()` calls with `logger.debug` in `pipeline.py`, `intelligence.py`, `tactical.py`, and `inventory.py`.
- Cleanly split `test_perf_api_snapshot.py` into CI comparison and `@pytest.mark.slow` stress tests.
- Added explicit empirical p95 and RSS delta limits to `test_perf_passive_scaling.py`, `test_perf_movement.py`, and `test_perf_resource.py`.
- Registered `integration`, `e2e`, and `strategic_loop` in `pyproject.toml`.
- Updated `test_perf_regression_baseline.py` to check authoritative baselines in `tests/perf/baselines/*.json`.

## Test Summary
- Unit tests (`pytest tests/unit`): 730 passed flawlessly, 0 warnings.
- Performance integrity tests (`pytest tests/perf -m "not slow"`): 48 passed flawlessly across all concurrent and local matrices.

## Files Changed
- `pyproject.toml`
- `src/core/dirty.py`
- `src/core/inventory.py`
- `src/engine/kernel.py`
- `src/engine/pipeline.py`
- `src/engine/pipeline_phases/capacity_enforcement.py`
- `src/engine/pipeline_phases/interactions.py`
- `src/engine/shop.py`
- `src/engine/tactical.py`
- `src/engine/town_resolution.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/systems/strategic_systems/redirection.py`
- `src/systems/world_systems/groups.py`
- `tests/perf/test_perf_api_snapshot.py`
- `tests/perf/test_perf_movement.py`
- `tests/perf/test_perf_passive_scaling.py`
- `tests/perf/test_perf_regression_baseline.py`
- `tests/perf/test_perf_resource.py`

## Completion Summary
All 8 milestones of the Performance Optimization Hardening plan have been fully executed and rigorously tested. The engine maintains 100% architectural integrity, zero hot-path print pollution, strict dirty set tracking parity, accurate budget enforcement, and pristine automated performance regression guards in CI.
