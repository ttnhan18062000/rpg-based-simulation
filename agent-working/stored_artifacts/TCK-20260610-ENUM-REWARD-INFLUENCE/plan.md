---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-ENUM-REWARD-INFLUENCE
artifact_type: plan
tags: [enum, reward, influence]
---

# Plan — TCK-20260610-ENUM-REWARD-INFLUENCE

## Ordered Steps

### Step 1 — Add `_region_owner_is_invader` helper to `influence.py`
File: `src/world/influence.py`
Add a module-level helper that converts a stored `Optional[int]` region owner to a faction_id string and checks `is_invader()` via `FactionSemanticsService`. Used to replace `region.owner_faction_id == Faction.MONSTER_HORDE` in the liberation check.

### Step 2 — Replace entity faction check in `process_influence_shift`
File: `src/world/influence.py`
Replace:
```python
if entity.identity.faction == Faction.HERO_GUILD:
    delta = -...
elif entity.identity.faction == Faction.MONSTER_HORDE:
    delta = +...
```
With:
```python
faction_id = get_faction_id_str(entity)  # handles both clean and legacy
semantics = get_faction_semantics_service()
if semantics.is_protector(faction_id):
    delta = -...
elif semantics.is_invader(faction_id):
    delta = +...
```
No EntityIdentityResolver needed here — `get_faction_id_str()` already handles clean properties and legacy enum fallback.

### Step 3 — Replace region owner check in `process_influence_shift`
File: `src/world/influence.py`
Replace `region.owner_faction_id == Faction.MONSTER_HORDE` with `_region_owner_is_invader(region.owner_faction_id)`.

### Step 4 — Replace region owner checks in `world_dynamics.py`
File: `src/engine/world_dynamics.py`
Replace:
- `region.owner_faction_id != Faction.HERO_GUILD` → `not _region_owner_is_protector(region.owner_faction_id)`
- `region.owner_faction_id != Faction.MONSTER_HORDE` → `not _region_owner_is_invader(region.owner_faction_id)`
Keep `owner_faction_id_set=Faction.HERO_GUILD` / `Faction.MONSTER_HORDE` unchanged (int assignment, not identity comparison).
Move the `from src.core.enums import Faction` import to top of the block (already present, no change needed for helpers).

### Step 5 — Add new tests
File: `tests/unit/world/test_influence.py`
Add 3 new test cases covering clean catalog path, invader faction path, and mixed legacy+clean coexistence.

## Scope Guards
- Do NOT change `WorldUpdate.owner_faction_id_set` type or assignment values
- Do NOT change `RegionState.owner_faction_id` type
- Do NOT change conquest/liberation thresholds
- Do NOT modify `process_conquest_lifecycle` — it compares authored data, not entity identity

## Dependency Map
Step 1 → Step 3, Step 4 (both use the helper)
Step 2 (independent, just entity-side)
Step 5 after Steps 2–4

## Deviations
<!-- Fill during implementation -->
