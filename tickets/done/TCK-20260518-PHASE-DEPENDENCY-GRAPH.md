# TCK-20260518-PHASE-DEPENDENCY-GRAPH

## Title

Implement Phase Dependency Graph for Dynamic Phase Skipping (Milestone 16)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a Phase Dependency Graph to dynamically schedule and skip pipeline phases based on expanded DirtySet analysis and system cadences, reducing unnecessary computation while maintaining byte-identical determinism.

## Scope

- Create `PhaseMetadata` dataclass defining inputs, outputs, cadence, and skip rules for each of the 17 authoritative phases.
- Implement `PhaseDependencyGraph` in `src/engine/phase_graph.py`.
- Integrate phase skipping logic into `AuthoritativeApplyPipeline.refine` in `src/engine/pipeline.py`.
- Record phase execution and skip counts in `StateUpdate.metric_counters`.
- Create unit test suite `tests/unit/optimization/test_phase_dependency_graph.py`.
- Create integration parity test suite `tests/integration/optimization/test_phase_skip_parity.py`.

## Out of Scope

- Adaptive Phase Budget Governor (Milestone 17).
- Changing internal subsystem business logic within individual phases.

## Acceptance Criteria

- Phase skip decisions are deterministic and observable via `StateUpdate.metric_counters`.
- Required phases (e.g., Compactor, Trust Boundary, Lifecycle) cannot be skipped.
- Optional phases skip when no relevant dirty domain entities exist.
- Optimized run with phase skipping exactly matches full reference run (100% hash parity).

## Related Tickets

- TCK-20260518-COMPONENT-PATCH-MODEL (Milestone 15)

## Related Docs

- `perf_plan_v2.md`
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/engine/pipeline.py`
- `src/engine/phase_graph.py`
- `src/core/updates.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Implemented dataclass PhaseMetadata and evaluation graph PhaseDependencyGraph.
- Integrated `run_phase` within `AuthoritativeApplyPipeline.refine` to log skips and executions in `StateUpdate.metric_counters`.

## Test Summary

- Added unit tests in `tests/unit/optimization/test_phase_dependency_graph.py` verifying dirty sets, cadence gating, and force-full-scan overrides (100% pass).
- Added integration parity tests in `tests/integration/optimization/test_phase_skip_parity.py` confirming byte-identical determinism and non-zero skip counts (100% pass).

## Files Changed

- `src/engine/phase_graph.py`
- `src/engine/pipeline.py`
- `tests/unit/optimization/test_phase_dependency_graph.py`
- `tests/integration/optimization/test_phase_skip_parity.py`

## Completion Summary

- Implemented Milestone 16 — Phase Dependency Graph for Dynamic Phase Skipping. Exposes exact state parity with significant performance optimization on clean/partial-dirty ticks.
