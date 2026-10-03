---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260517-STATE-UPDATE-COMPACTOR
artifact_type: plan
tags: [state, update, compactor]
---

# Implementation Plan: StateUpdateCompactor

## Proposed Changes

### 1. `src/engine/compactor.py` (NEW)
Create `StateUpdateCompactor` and `CompactionMetrics`.
- Implement `compact(state: AuthoritativeState, update: StateUpdate) -> StateUpdate`.
- Implement `compact_with_metrics(state: AuthoritativeState, update: StateUpdate) -> tuple[StateUpdate, CompactionMetrics]`.

### 2. `src/engine/pipeline.py` (MODIFY)
In `AuthoritativeApplyPipeline.refine()`, integrate `StateUpdateCompactor.compact(state, update)` as the first step of Phase 1 to strip redundant updates early.

### 3. Unit Tests & Perf Regression
- Create `tests/unit/optimization/test_state_update_compactor.py` covering tests 5.1 through 5.6.
- Create `tests/perf/test_apply_compaction_perf.py` verifying compaction reduces update count in a 1000-entity movement scenario.

## Verification Plan
1. `pytest tests/unit/optimization/test_state_update_compactor.py -v`
2. `pytest tests/perf/test_apply_compaction_perf.py -v`
3. Fast unit test suite: `pytest tests/unit/ -m "not slow" -v`
4. Parity test: `pytest tests/perf/test_dirty_parity.py -v`
