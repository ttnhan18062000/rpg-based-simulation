# Investigation: TCK-20260403-FINAL-CONVERGENCE

## Findings

### 1. PydanticUserError (Circular Dependency)
- **Problem**: `CombatAspect` (in `combat.py`) depends on `CombatTraceUpdate` (in `base.py`) for trace records. `CombatTraceUpdate` depends on `CombatAspect` (via `ActionProposal` / `Entity`).
- **Impact**: This circularity causes Pydantic 2.x to fail during `model_rebuild()` because the types are not fully available in the module scope at the time of resolution.
- **Traceback**:
  ```python
  pydantic.errors.PydanticUserError: `Entity` is not fully defined; you should define `StatusEffect`, then call `Entity.model_rebuild()`.
  ```
- **Analysis**: Eagerly calling `model_rebuild()` in `entity.py` fails because `CombatAspect` (part of Entity) needs a type from `base.py` that hasn't finished loading.

### 2. Deep Recursive Immutability
- **Problem**: Standard `SimulationModel.freeze()` only froze the first level. `list` and `dict` fields remained mutable.
- **Solution**: Implemented `_freeze_recursive` using `MappingProxyType` and `tuple`.
- **Status**: Logic implemented in `base.py`, but needs validation against Pydantic serialization.

### 3. Transport Payload Consolidation
- **Problem**: `EngineManager` had separate paths for `compact` and `rich` payloads, causing redundant compute and potential divergence.
- **Solution**: Consolidate into a single tick publication cycle with thread-safe caches.

## Risks & Assumptions
- **Assumption**: Moving trace records to a shared `src/core/models/combat.py` will break the import loop without breaking business logic.
- **Risk**: Performance impact of deep `freeze()` on large simulation snapshots.
- **Risk**: Pydantic serialization warnings for `MappingProxyType` might return if `model_serializer` isn't robust.

## Existing Patterns to Reuse
- Use the established `Aspect` composition pattern in `Entity`.
- Use the `IntentUpdate` pipeline in `ActionSystem`.
