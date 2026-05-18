# Implementation Plan: Milestone 11 - Logic Hardening

## Goal
Formalize the 17-phase `AuthoritativeApplyPipeline` to ensure every simulation tick follows a deterministic, causally-consistent sequence of refinement.

## User Review Required
> [!IMPORTANT]
> This milestone involves a major refactor of `src/engine/pipeline.py` to strictly follow the 17-phase sequence. While it aims for 100% parity, the reordering of some minor phases (e.g., social vs tactical) might cause edge-case hash mismatches that require reconciliation.

## Proposed Changes

### Engine Pipeline
#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- Refactor `refine()` to implement the 17 phases in exact order.
- Remove redundant duplicate code blocks.
- Add explicit logging/telemetry for each phase transition.

### Pipeline Phases
#### [NEW] [actor_validity.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline_phases/actor_validity.py) (if missing/incomplete)
- Implement `status_sleeping` check.
- Reject all intents for incapacitated actors.

### Core State
#### [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Ensure `RejectionRegistry` is properly typed and accessible during the `refine()` phase.

## Verification Plan

### Automated Tests
- `pytest tests/engine/pipeline/`: Verify phase execution order and rejection logic.
- `pytest tests/parity/`: Ensure bit-identical results for established scenarios.
- `python scripts/check_determinism.py`: Verify multi-core execution parity.

### Manual Verification
- Review `AuthoritativeState.rejection_registry` in a long-running stress test to ensure no "silent" rejections occur.
