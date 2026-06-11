---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260331-RUNTIME-INTEGRITY
artifact_type: plan
tags: [runtime, integrity]
---

# Implementation Plan: TCK-20260331-RUNTIME-INTEGRITY

## Step-by-Step Approach

### Phase 1: Legacy Access Elimination (The "Big Clean")
1.  **System Audit**: Systematically update `src/systems/` to use typed aspects.
    - `economy_system.py`: Update HP and gold access.
    - `hero_lifecycle_system.py`: Update level, death_count, and HP access.
    - `progression_system.py`: Update stamina and AI state access.
    - `telemetry_system.py`: Update gold and level access.
2.  **AI Audit**: Update `src/ai/` to use typed aspects.
    - `ai/goals/base.py`: Update HP ratio access.
    - `ai/states.py`: Update HP, gold, stamina, and state access.
3.  **Utility Audit**: Update `src/utils/replay.py` and others.

### Phase 2: AI Decision Purity
1.  **Refactor handlers in `ai/states.py`**:
    - Convert `actor.stats.gold += price` (direct mutation) into `ActionProposal(verb=ActionType.TRADE, ...)` or include it in the `intent_metadata`.
    - Ensure all items/gold transfers are proposed, not applied.
2.  **Enforce Read-Only in `AIBrain.decide()`**:
    - Add a temporary assertion or flag to detect mutations during worker execution if possible.

### Phase 3: WorldLoop & Worker Fixes
1.  **Fix Inline Dispatch**: Ensure `WorldLoop` always passes `entity.copy()` or a snapshot-wrapped entity to the worker, even in inline mode.
2.  **Snapshot Immuntability**: Wrap snapshot collections in `ReadonlyProxy` or similar if not already effectively immutable.

### Phase 4: API & Presentation Convergence
1.  **Update `src/api/routes/state.py`**: 
    - Use `EntityPresenter.present_slim(entity)` for the main stream.
    - Use `EntityPresenter.present_full(entity)` for the inspector.
2.  **Refactor/Remove `src/api/encoder.py`**: Align it with the aspect model or merge its logic into the presenters.

### Phase 5: Verification
1.  Run the full test suite (`pytest tests/`).
2.  Self-correct any `AttributeError` or `KeyError` arising from missing shims.
3.  Verify determinism with `tests/integration/test_determinism.py`.

## Affected Components
- `src/core/entities/entity.py` (Verify no shims)
- `src/systems/*` (Call sites)
- `src/ai/*` (Call sites + handler logic)
- `src/api/*` (Routes + presentation)
- `src/engine/world_loop.py` (Worker dispatch)
