# Implementation Plan: TCK-20260403-FINAL-CONVERGENCE

## Goal
Achieve full architectural stability and 100% test pass rate for the AOA simulation engine by resolving circular dependencies and hardening deep immutability.

## Proposed Changes

### 1. Decoupling & Cycle Breaking (Architectural Pivot)
#### [NEW] `src/core/models/combat.py`
- Authoritative `CombatTraceRecord` and `CombatTraceDetails`.
- No dependencies on `src/actions/base.py`.

#### [MODIFY] `src/core/aspects/combat.py`
- Import types from `src/core/models/combat.py`.
- Restore eager `model_rebuild()`.

#### [MODIFY] `src/actions/base.py`
- Refactor `CombatTraceUpdate` to use shared `CombatTraceRecord`.
- Drop the failing centralized rebuild orchestrator; return to standard file-bottom rebuilds.

#### [MODIFY] `src/core/entities/entity.py` & `src/core/models/snapshot.py`
- Restore eager `model_rebuild()`.

### 2. Deep Immutability & Serialization
#### [MODIFY] `src/core/models/base.py`
- Implement robust `model_serializer` to handle `MappingProxyType` and other frozen types.
- Ensure `model_copy(deep=True)` correctly unfreezes nested collections for simulation transitions.

### 3. Infrastructure & Transport
#### [MODIFY] `src/api/engine_manager.py`
- Unify WebSocket payload caching (`compact`/`rich`) and Redis delta state.
- Ensure thread-safe atomicity in tick publication.

### 4. Strict Typing Cleanup
#### [MODIFY] `src/core/models/types.py`
- Narrow `TargetUnion` to specific supported types (int, Vector2, etc.).

## Data Flow / Architecture
- **In-Game Flow**: `WorldLoop` -> `Snapshot.from_world()` (Recursive Freeze) -> `EngineManager` (Transport) -> `WorldPresenter` (Serialization).
- **Update Flow**: `ConflictResolver` -> `ActionProposal` (Validated) -> `SimulationModel.copy()` (Unfreeze) -> Mutation (Temporary) -> `freeze()`.
