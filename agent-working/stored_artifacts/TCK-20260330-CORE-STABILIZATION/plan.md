---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260330-CORE-STABILIZATION
artifact_type: plan
tags: [core, stabilization]
---

# Implementation Plan: TCK-20260330-CORE-STABILIZATION (Strict Refactor Follow-up)

## Objective
Finalize the Core Architecture Stabilization by completing the AI memory pipeline, extracting Engine phases, and implementing deterministic validation, strictly adhering to `reviews/2.refactor_plan.md`.

## User Review Required
> [!IMPORTANT]
> **Primary Plan Alignment**: This implementation strictly follows the priority order and constraints of the primary plan at `reviews/2.refactor_plan.md`.
> **Breaking Change**: Domain models will no longer own `to_slim_schema` or `to_full_schema`. These are being extracted into a dedicated Presenter layer.

## Proposed Changes

### Phase 1: AI Decision Purity (Step 4 of Primary Plan)
- [ ] **AIBrain Memory Phase**: Complete the appraisal logic to propose removals of dead or out-of-range entities via `intent_metadata`.
- [ ] **ActionSystem Integration**: Ensure `_apply_intent_metadata` handles memory cleanup and "recover" hooks correctly.
- [ ] **Purity Audit**: Verify no `AIBrain` handler performs direct state mutation on `actor` or `snapshot`.

### Phase 2: Engine Phase Extraction (Step 7 of Primary Plan)
- [ ] **Engine Decomposition**: Create `src/engine/phases/` and extract `SchedulingPhase`, `CollectionPhase`, `ResolutionPhase`, `CleanupPhase`, `PersistencePhase`.
- [ ] **Visible Orchestration**: Update `WorldLoop._step` to act as a pure coordinator of these phases.

### Phase 3: Domain vs. API Separation (Steps 1.3 & 8 of Primary Plan)
- [ ] **Presenter Layer**: Create `src/api/presenters/entity.py`.
- [ ] **Refactoring Entity**: Remove `to_schema` and `_serialize` methods from `src/core/entities/entity.py`.
- [ ] **Updating Call Sites**: Update the API layer to use the new presenters.

### Phase 4: Deterministic Validation (Step 9 of Primary Plan)
- [ ] **Hashing Logic**: Implement `WorldState.compute_hash()` for stable state snapshots.
- [ ] **Replay Sync**: Add test cases for hash stability at T=100/500/1000.

### Phase 5: Reducing Legacy Shims (Step 10 of Primary Plan)
- [ ] **Legacy Purge**: Remove re-exports in `src/core/__init__.py`.
- [ ] **Forced Migration**: Update any remaining call sites to use explicit aspect paths.

## Verification Plan

### Automated Tests
- `pytest tests/unit/ai/test_cognitive_pipeline.py`: Verify side-effect-free decisions.
- `pytest tests/unit/engine/test_world_loop_phases.py`: Verify phase execution order.
- `pytest tests/integration/test_determinism_aoa.py`: Verify hash stability.
- Full regression: `pytest tests/` (All 748 tests passing).

### Manual Verification
- Code audit of `src/core` for any remaining `dict[str, Any]` dynamic aspects.
- Verification of API serialization through the new presenter layer.
