---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260518-PHASE-BUDGET-GOVERNOR
phase: done
date: 2026-05-18
tags: [phase, budget, governor]
---

# TCK-20260518-PHASE-BUDGET-GOVERNOR

## Title

Implement Adaptive Phase Budget Governor (Milestone 17)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement an adaptive Phase Budget Governor that monitors recent per-phase compute costs (p95 latency, tick cost, work debt) and dynamically throttles sub-phase candidate budgets, scan policies, and background sweep intervals under system pressure without skipping correctness-critical simulation work.

## Scope

- Implement `ScanPolicy`, `PhaseBudgets`, and `PhaseBudgetGovernor` in `src/engine/phase_governor.py`.
- Integrate `PhaseBudgetGovernor` into `V2EngineManager` to evaluate phase costs at each tick.
- Update `GovernorPolicy` to include `strategic_budget`, `movement_budget`, `background_sweep_interval`, `compaction_level`, and `scan_policy`.
- Update `StrategicWorkQueue.build` to consume `strategic_budget` and `background_sweep_interval`.
- Update `MovementCandidateSelector.select` to consume `movement_budget` and `scan_policy`.
- Create unit test `tests/unit/optimization/test_phase_budget_governor.py`.

## Out of Scope

- Milestone 18 Long-Run Stability Certification.
- Changing foundational subsystem combat or economic formulas.

## Acceptance Criteria

- Governor lowers optional candidate work (strategic wander, routine sweeps) under compute pressure.
- Urgent work (failed path, unresolved blockers, emergencies) still runs under pressure.
- Degraded mode remains 100% deterministic across identical runs.
- Full budget recovery occurs when pressure drops below recovery watermarks.
- No correctness-critical phase (lifecycle, transactions, capacity, quest finalization) is skipped or deferred.

## Related Tickets

- TCK-20260518-PHASE-DEPENDENCY-GRAPH (Milestone 16)

## Related Docs

- `perf_plan_v2.md`
- `docs/engine/performance_contract.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260518-PHASE-BUDGET-GOVERNOR/`

## Related Code Areas

- `src/engine/phase_governor.py`
- `src/engine/policy.py`
- `src/engine/governor.py`
- `src/engine/candidate_selector.py`
- `src/systems/strategic_systems/work_queue.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Defined `ScanPolicy` (`FULL`, `THROTTLED`, `EXACT_DIRTY`) to bypass O(N) entity scans under compute pressure and evaluate only dirty subset.
- Propagated `PhaseBudgets` through `GovernorPolicy` and `ResourceGovernor`.
- Protected urgent/dirty candidate evaluation across movement and strategic subsystems.

## Test Summary

- `pytest tests/unit/optimization/test_phase_budget_governor.py` (7 tests passed in 0.23s).
- `pytest tests/unit/optimization/` (79 tests passed in 0.48s).

## Files Changed

- `src/engine/phase_governor.py`
- `src/engine/policy.py`
- `src/engine/governor.py`
- `src/engine/candidate_selector.py`
- `src/systems/strategic_systems/work_queue.py`
- `tests/unit/optimization/test_phase_budget_governor.py`
- `docs/engine/performance_contract.md`

## Completion Summary

- Milestone 17 Adaptive Phase Budget Governor fully implemented and verified. The engine now dynamically modulates sub-phase candidate scan rigor, spatial routing budgets, and background entity sweep intervals in response to compute pressure signals, robustly shielding core determinism and p95 latency envelopes.
