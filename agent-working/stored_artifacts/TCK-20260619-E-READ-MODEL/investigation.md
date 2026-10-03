# Investigation: TCK-20260619-E-READ-MODEL

## Current Behavior

### Existing presenter layer
- `src/api/presenters/state_presenter.py` — `StatePresenter` with `present_minimal()`, `present_full()`, `present_entity()`, `present_region()`
- `src/api/read_model_cache.py` — `ReadModelCache` wraps StatePresenter with dirty-set-driven invalidation
- `src/api/engine_manager.py` — `V2EngineManager.get_state()`, `get_full_snapshot()`, `get_entities_paged()`, `get_entity()` all route through ReadModelCache → StatePresenter ✓

### Routes audit
- `server.py` inline routes → `manager.get_state/get_full_snapshot/get_entities_paged/get_entity()` → shaped ✓
- `routes/behavior.py` → `LocalWarehouseAdapter` (no direct state) ✓
- `routes/history.py`, `routes/search.py` → warehouse adapter ✓
- `ws/stream.py` → **VIOLATION**:
  - Line 14: `from src.core.state import AuthoritativeState` (unused but present)
  - Line 128: `state = manager._latest_state` — direct private raw state access
  - Lines 129-132: reads `state.entities[entity_id].timeline` directly

### Fix for ws/stream.py
Add `get_entity_timeline_events(entity_id)` to `V2EngineManager` (internal access is fine within manager). Remove unused import from stream.py. Use the new method.

### ReadModelService design
Thin facade wrapping the existing pattern into a unified documented interface. Routes don't need to change (already compliant via manager methods). ReadModelService codifies what's already happening and provides a stable import point for future routes.

## Architecture Guard Scope
Check that no file in `src/api/routes/`, `src/api/ws/`, or `src/api/server.py` imports `AuthoritativeState` or `EntityState` from `src.core.state` outside a `TYPE_CHECKING` block.

After fixing ws/stream.py, all files will be clean.

## Parity
New parity entry INFRA-210.
