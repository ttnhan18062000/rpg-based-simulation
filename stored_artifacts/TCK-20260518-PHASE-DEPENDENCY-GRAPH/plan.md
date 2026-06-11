---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260518-PHASE-DEPENDENCY-GRAPH
artifact_type: plan
tags: [phase, dependency, graph]
---

# Phase Dependency Graph Implementation Plan (Milestone 16)

## Goal
Implement `PhaseMetadata` and `PhaseDependencyGraph` in `src/engine/phase_graph.py` and integrate them into `AuthoritativeApplyPipeline.refine()` in `src/engine/pipeline.py` to enable dynamic phase skipping on quiet ticks.

## Status: DONE

## Design
1. **PhaseMetadata & PhaseDependencyGraph**: Registered all 17 simulation phases with input/output domain requirements, cadence gating properties, and unconditional execution flags.
2. **Pipeline Integration**: Replaced unconditional phase method calls in `AuthoritativeApplyPipeline.refine()` with a dynamic `run_phase` wrapper that checks `PhaseDependencyGraph.should_run_phase(...)`.
3. **DirtySet Tracking**: Enhanced `DirtySetBuilder.mark_from_update` in `src/core/dirty.py` to track `NavigationUpdate` and `TaskUpdate` proposals.
4. **Metrics**: Recorded `phase_runs`, `phase_skips`, and per-phase execution statistics in `StateUpdate.metric_counters`.

## Verification Results
- Unit tests (`tests/unit/optimization/test_phase_dependency_graph.py`) passed 5/5.
- Integration parity tests (`tests/integration/optimization/test_phase_skip_parity.py`) passed 1/1, proving 100% exact state hash parity across 10 simulation ticks while verifying non-zero phase skip counts.
- Full optimization suite passed 82/82.
