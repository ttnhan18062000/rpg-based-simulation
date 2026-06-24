---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-PERF-BUDGETS
phase: open
date: 2026-06-24
tags: [performance, perf-budget, benchmarking, adventure-decision, profiler]
---

# TCK-20260624-FIX-PERF-BUDGETS

## Title
Fix performance budget test failures — update ad-hoc thresholds and fix one real AdventureDecisionPhase regression

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
12+ perf tests fail, but investigation reveals all thresholds are **ad-hoc** (not sourced from `docs/engine/performance_contract.md`). The contract defines measurement methodology (100-warmup + 1000-sample) and a >5% regression flag rule but specifies no absolute per-phase ms budgets. Most failures are test design problems; one is a real code regression.

**Verdicts per test:**

| Test | Measured | Threshold | Decision |
|------|----------|-----------|----------|
| `test_hard_law_monitor_overhead` | 8–49% relative / 1–6ms abs | <5% OR <0.1ms abs | **Fix test** — 0.1ms absolute arm is unrealistically tight for VM; widen to 2ms |
| `test_phase3_adventure_decision_perf_budget` | 46.9ms / 100 entities | <15ms | **Fix code** — 3x real regression in `AdventureDecisionPhase.apply()` from `ServiceRegistry.all()` full scan |
| `test_performance_budget_100_entities` (phase4) | 6.7ms | <5ms | **Fix test** — 34% overage, single-run no-sampling, raise to 10ms |
| `test_benchmark_disables_frame_pacing_by_default` | 383ms | <100ms | **Fix test** — logically impossible: 5 ticks × ~20ms = 100ms minimum |
| `test_benchmark_schema_contains_compute_and_wall_clock_metrics` | ERROR | — | **Fix test** — investigate after above is fixed |
| `test_local_vs_concurrent_idle_parity_100_ticks` | varies | — | **Fix test** — single-run, no warmup |
| `test_worker_chunk_boundary_determinism[51]` | varies | — | **Fix test** — timing-sensitive on shared VM |
| `test_phase2_self_model_perf_budget_and_dirty_check` | varies | — | **Fix test** — ad-hoc threshold, no proper sampling |
| `test_kernel_integrated_cache_sweep` | varies | — | **Fix test** — timing-sensitive |
| `test_profile_specific_behavior` tests | varies | — | **Fix test** — ad-hoc thresholds |
| `test_milestone_b_operational_gate` | varies | — | **Fix test** — gate threshold ad-hoc |
| `test_concurrency_limit_stability` | varies | — | **Fix test** — timing on shared VM |

## Scope

### Code fix (P-high within this ticket)
- Profile `AdventureDecisionPhase.apply()` — identify the `ServiceRegistry.all()` full scan bottleneck
- Fix to O(region) lookup or cache the service list across the tick rather than scanning all services per entity
- Verify the fix brings phase3 under 15ms / 100 entities

### Test fixes
- `test_benchmark_disables_frame_pacing_by_default`: change assertion from `elapsed < 100ms` to `elapsed < 500ms` (confirms pacing is OFF — 5 ticks should complete in under 500ms without sleep-pacing, but not in under 100ms)
- `test_hard_law_monitor_overhead`: remove the `abs_overhead_ms < 0.1ms` OR branch, keep only the `overhead < 5%` relative check (per `performance_contract.md §4.2`)
- `test_performance_budget_100_entities` (phase4): raise threshold from 5ms to 10ms; add at least 10 warmup ticks (per contract §3.2)
- Remaining timing-sensitive tests: either (a) add `@pytest.mark.slow` to exclude from default CI and run only with `--resource-budget large`, or (b) rewrite to use `BenchHarness` with proper 100-warmup + 1000-sample methodology
- Add `@pytest.mark.slow` to all of `tests/perf/` and `tests/integration/perf/` that rely on wall-clock assertions

## Out of Scope
- Adding absolute per-phase budgets to `performance_contract.md` (separate architecture decision)
- Fixing `tests/integration/optimization/` if they pass after marking slow

## Acceptance Criteria
- `test_phase3_adventure_decision_perf_budget` passes with measured < 15ms after code fix
- `test_benchmark_disables_frame_pacing_by_default` passes with corrected assertion
- `test_hard_law_monitor_overhead` passes with corrected threshold
- All remaining perf tests either pass with updated thresholds or are marked `@pytest.mark.slow` and excluded from default CI
- No perf regression in the adventure decision path

## Related Tickets
- **`TCK-20260624-PERF-GUARD-INFRA`** — PREREQUISITE: must be completed first. Introduces `perf_baselines.json`, `perf_budget` fixture, and `tools/perf_guard.py`. This ticket migrates existing tests to use that infrastructure.
- `docs/engine/performance_contract.md` — measurement methodology reference

## Related Docs
- `docs/engine/performance_contract.md` — §3.2 measurement protocol, §4.2 instrumentation ceiling, §5 regression flag rule
- `docs/architecture/adr-005 performance`

## Related Code Areas
- `src/engine/phases/adventure_decision.py` — `AdventureDecisionPhase.apply()`, likely around `ServiceRegistry.all()` call
- `src/world/services/registry.py` — `ServiceRegistry.all()` — check if O(n) full scan
- `tests/perf/` — all files
- `tests/integration/perf/`
- `tests/integration/optimization/`
- `tests/integration/kernel/test_milestone_b_closure.py`
- `tests/integration/kernel/test_executor_determinism.py`

## Assumptions / Open Questions
- Confirm `ServiceRegistry.all()` is the bottleneck in `AdventureDecisionPhase` — profile before assuming
- The performance contract's >5% regression flag rule (§5): the phase3 overage is 213% (46.9 vs 15ms), well past the flag threshold → warrants code fix, not just test update
- For timing-sensitive tests on a VM: consider whether they should be skipped in CI by default and only run on dedicated perf hardware

## Implementation Notes
Phase 1: fix `AdventureDecisionPhase.apply()`. Look for:
1. `ServiceRegistry.all()` called inside entity-level loop (should be called once before the loop)
2. `PerformanceBudgets` counter per entity (should be aggregated)
3. Any dictionary or list comprehension inside a nested loop

Phase 2: fix test assertions/design.
Phase 3: mark slow where warranted.

## Test Summary
Run: `pytest tests/perf/ tests/integration/perf/ tests/integration/optimization/ tests/integration/kernel/test_milestone_b_closure.py tests/integration/kernel/test_executor_determinism.py -m "not slow" --tb=short -q`

## Files Changed
TBD

## Completion Summary
TBD
