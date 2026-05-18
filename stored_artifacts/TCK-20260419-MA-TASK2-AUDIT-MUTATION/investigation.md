# Investigation: Authoritative Mutation Audit

## Current State of Mutation

### Member Immutability
- `AuthoritativeState` and `EntityState` are `dataclasses` with `frozen=True`.
- This prevents direct assignment like `state.tick = 10`.
- However, members like `entities: Dict[int, EntityState]` and `properties: Dict[str, Any]` are NOT frozen. They can be mutated via `state.entities[id] = ...` or `ent.properties["key"] = val`.

### Apply Path (`src/engine/apply.py`)
- `ApplyPath.apply_generation` correctly creates NEW generations using `replace`.
- It uses `dict(prior_state.entities)` to clone the top-level collection.
- Issue: Nested `properties` dict in `EntityState` is cloned using `dict(entity.properties)` in `_apply_entity_update`. This is a shallow copy. If `properties` contains nested dicts/lists, they are shared across generations.

### Kernel Leaks (`src/engine/kernel.py`)
- `_phase_collection` passes the `subject` (EntityState) to `WorkerPacket`.
- The `subject` is a reference to an object in the current tick's `AuthoritativeState`.
- If a worker (synchronous or asynchronous) mutates `subject.properties`, it affects the authoritative state immediately, which violates the "Resolution" phase boundary (Phase 4).

### Scheduler and Helpers
- `DeterministicScheduler` only reads from state.
- `CanonicalStateHasher` only reads from state and uses `sort_keys=True` in `json.dumps` (redundantly, since `to_canonical_data` already sorts).

## Targeted Refactors

1. **Kernel Insulation**: Ensure that `EntityState` objects passed to workers are either deep-copied or strictly accessed as read-only. Given Milestone A's "law set," we should verify this with tests.
2. **Apply Path Hardening**: Ensure `AuthoritativeState members` are truly isolated after `apply_generation`.
3. **Immutability Enforcement**: Add a `Law` check or test that fails if an authoritative state member is mutated.

## Discovered Mutations
- None found so far in the current codebase (it's very clean), but the *potential* for hidden mutation is high due to shallow copies.
