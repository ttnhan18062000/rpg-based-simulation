# TCK-20260518-PHASE-DEPENDENCY-GRAPH

## Title

Implement Phase Dependency Graph for Dynamic Phase Skipping (Milestone 16)

## Status

DONE

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

- Phase skip decisions are deterministic and observable via `StateUpdate.metric_counters`. (Verified)
- Required phases (e.g., Compactor, Trust Boundary, Lifecycle) cannot be skipped. (Verified)
- Optional phases skip when no relevant dirty domain entities exist. (Verified)
- Optimized run with phase skipping exactly matches full reference run (100% hash parity). (Verified)

## Related Tickets

- TCK-20260518-COMPONENT-PATCH-MODEL (Milestone 15)

## Related Docs

- `perf_plan_v2.md`
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260518-PHASE-DEPENDENCY-GRAPH/plan.md`
- `stored_artifacts/TCK-20260518-PHASE-DEPENDENCY-GRAPH/investigation.md`
- `stored_artifacts/TCK-20260518-PHASE-DEPENDENCY-GRAPH/test_plan.md`

## Related Code Areas

- `src/engine/pipeline.py`
- `src/engine/phase_graph.py`
- `src/core/dirty.py`
- `src/core/updates.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Tracked `NavigationUpdate` and `TaskUpdate` proposals in `DirtySetBuilder.mark_from_update` to ensure seamless dirty set propagation across multi-tick AI and movement behaviors.
- Wrapped all optional phase invocations in `refine` with a dynamic `run_phase` closure that checks `PhaseDependencyGraph.should_run_phase` and records execution and skip counts directly to `metric_counters`.

## Test Summary

- `pytest tests/unit/optimization/test_phase_dependency_graph.py` (5/5 passed, 0.29s)
- `pytest tests/integration/optimization/test_phase_skip_parity.py` (1/1 passed, 0.24s)
- `pytest tests/unit/optimization/ tests/integration/optimization/` (82/82 passed, 0.72s)

## Files Changed

- `src/engine/phase_graph.py` (new)
- `src/engine/pipeline.py`
- `src/core/dirty.py`
- `tests/unit/optimization/test_phase_dependency_graph.py` (new)
- `tests/integration/optimization/test_phase_skip_parity.py` (new)

## Completion Summary

- Successfully implemented the Phase Dependency Graph and integrated it into the authoritative simulation pipeline. The engine now dynamically skips unneeded phase evaluations on quiet ticks while maintaining 100% exact simulation state hash parity and recording granular metrics.
