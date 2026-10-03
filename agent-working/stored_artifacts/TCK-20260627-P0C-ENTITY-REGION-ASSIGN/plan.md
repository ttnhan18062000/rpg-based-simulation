---
ticket_id: TCK-20260627-P0C-ENTITY-REGION-ASSIGN
phase: plan
---

# Plan: Fix navigation.region_id assignment at world compile

## Ordered Steps

### Step 1 — Fix WorldCompiler.compile() to assign navigation.region_id

**File**: `src/worldbuilding/compiler.py`
**Lines**: 315-337 (the V2EntityBuilder chain inside `if region:` block)

Change: add `.navigation(region_id=region_id)` to the builder chain after `.location(float(x), float(y))`.

`region_id` is already in scope (line 254: `region_id = pop_spec.spawn_region`), guaranteed non-empty because we're inside the `if region:` guard.

**Before**:
```python
builder = (
    V2EntityBuilder(next_entity_id)
    .kind(pop_spec.role.lower())
    .location(float(x), float(y))
    .identity(...)
    .combat(...)
    .lifecycle(active=True)
)
```

**After**:
```python
builder = (
    V2EntityBuilder(next_entity_id)
    .kind(pop_spec.role.lower())
    .location(float(x), float(y))
    .navigation(region_id=region_id)
    .identity(...)
    .combat(...)
    .lifecycle(active=True)
)
```

### Step 2 — Add post-compile assertion test

**File**: `tests/integration/worldassembly/test_e2e_smoke.py`

Add a new test `test_urban_political_all_entities_have_region_id()` that compiles `urban_political` and asserts `all(e.navigation.region_id is not None for e in state.entities.values())`.

Also add the same assertion to the other world smoke tests to prevent drift in other compositions.

### Step 3 — Update ticket Implementation Notes

**File**: `tickets/inprogress/TCK-20260627-P0C-ENTITY-REGION-ASSIGN.md`

## Files to Change Per Step

| Step | File | Change |
|---|---|---|
| 1 | `src/worldbuilding/compiler.py` | Add `.navigation(region_id=region_id)` to builder chain |
| 2 | `tests/integration/worldassembly/test_e2e_smoke.py` | New test asserting all entities have non-None region_id |
| 3 | `tickets/inprogress/TCK-20260627-P0C-ENTITY-REGION-ASSIGN.md` | Update Implementation Notes |

## Explicit Scope Guards

- Do NOT touch `src/worldassembly/entity_spawner.py` — out of scope (separate pipeline)
- Do NOT touch `src/worldassembly/models.py` — no `spawn_region` field needed on `ResolvedEntityProfile` for this fix
- Do NOT touch `src/entities/archetype_factory.py` — out of scope
- Do NOT touch `src/worldassembly/resolver.py` — spawn_region already correctly set upstream

## Dependency Map

Step 1 → Step 2 (test verifies the fix) → Step 3 (ticket housekeeping)

## AC-to-Step Mapping

| AC | Step |
|---|---|
| After `WorldCompiler.compile()`, every entity has `navigation.region_id is not None` | Step 1 |
| `make world-compile WORLD=urban_political` succeeds | Step 1 (already passes; fix makes the assertion also pass) |
| Test asserts `all(e.navigation.region_id is not None ...)` | Step 2 |
| Existing world assembly tests pass | Step 1 (non-breaking, additive) |

## Deviations

(none yet)
