# Implementation Plan: TCK-20260401-FINAL-CONVERGENCE

## Goal
Achieve full architectural convergence by addressing partially implemented tasks related to action application, API presentation, and aspect data ownership.

## User Review Required
> [!IMPORTANT]
> This plan proposes moving nearly all action application logic into a unified utility or service to ensure that Replay/Recovery and Live Simulation are identical. This might involve a small refactor of `ConflictResolver` to not do "instant" applications, or providing a shared way to "fully apply" a validated proposal.

## Proposed Changes

### 1. Unified Action Pipeline
- **Problem**: `ConflictResolver` applies some actions immediately, while `ActionSystem` applies others later. `EngineManager` recovery only calls `ConflictResolver`, missing the late-stage applications.
- **Solution**: Move all verb-specific application logic into a `UniversalApplier` or ensure `ActionSystem` logic is reachable and called during recovery.
- **Files**:
  - `src/systems/gameplay/action_system.py`
  - `src/engine/conflict_resolver.py`
  - `src/api/engine_manager.py` (to ensure recovery calls the full application pipeline)

### 2. API Presenter Convergence
- **Problem**: `src/api/routes/state.py` performs manual serialization for many world objects, violating the presenter layer pattern.
- **Solution**: Create dedicated presenters for World objects (ResourceNodes, Chests, GroundItems, Events).
- **Files**:
  - [NEW] `src/api/presenters/world_presenter.py`
  - [NEW] `src/api/presenters/event_presenter.py`
  - [MODIFY] `src/api/routes/state.py`: Replace manual loops with presenter calls.

### 3. Mind Aspect Consistency
- **Problem**: Some legacy code might still use "flat" access to `mind` properties.
- **Solution**: Audit and refactor `src/ai/states/town.py` and other AI logic to ensure all accesses are via `mind.decision`, `mind.emotion`, etc.
- **Files**:
  - `src/ai/states/town.py`
  - `src/ai/states/interaction.py`

### 4. Infrastructure & Caching
- **Problem**: Introspection/Rendering layer needs stabilization and possibly caching for high-density simulations.
- **Solution**: Implement basic caching in presenters or at the route level for static data.
- **Files**:
  - `src/api/routes/state.py`

## Verification Plan

### Automated Tests
- `pytest tests/e2e/test_deterministic_replay.py`: Ensure live simulation remains deterministic.
- [NEW] `tests/unit/engine/test_recovery_consistency.py`: Specifically test that replaying `LOOT` / `HARVEST` actions via `EngineManager` recovery logic produces the same state as live.

### Manual Verification
- Use the UI to verify that world objects (nodes, chests) are still rendered correctly after migration to the `WorldPresenter`.
