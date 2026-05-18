# Implementation Plan - Phase Dependency Graph (Milestone 16)

## Purpose
Dynamically schedule and skip pipeline phases based on expanded DirtySet analysis and system cadences to reduce unnecessary computation while ensuring 100% byte-identical determinism.

## Proposed Changes

### 1. `src/engine/phase_graph.py`
- Define `PhaseMetadata` dataclass.
- Implement `PhaseDependencyGraph` tracking all 17 authoritative phases.
- Implement `should_run_phase` method.

### 2. `src/engine/pipeline.py`
- Refactor `AuthoritativeApplyPipeline.refine` to evaluate phase skip decisions.
- Record execution and skip metrics in `metric_counters`.

## Verification Plan
- Unit test suite: `tests/unit/optimization/test_phase_dependency_graph.py`.
- Integration parity test suite: `tests/integration/optimization/test_phase_skip_parity.py`.
- Verify REST API parity and benchmark performance.
