---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-ENUM-REWARD-INFLUENCE
artifact_type: investigation
tags: [enum, reward, influence]
---

# Investigation — TCK-20260610-ENUM-REWARD-INFLUENCE

## Current Behavior

### `src/world/influence.py`

`FactionInfluenceService.process_influence_shift()` (lines 25-45):
- Checks `entity.identity.faction == Faction.HERO_GUILD` / `Faction.MONSTER_HORDE` directly
- Sets `w_upd_args["owner_faction_id_set"] = Faction.MONSTER_HORDE` (conquest) or `-1` (liberation sentinel)
- Liberation check: `region.owner_faction_id == Faction.MONSTER_HORDE` — compares stored int with enum

`process_conquest_lifecycle()` (lines 47-90):
- `w_upd.owner_faction_id_set == Faction.MONSTER_HORDE` — checks the set value
- `w_upd.owner_faction_id_set == -1` — liberation sentinel check
- These remain as-is (data model layer, not identity classification)

### `src/engine/world_dynamics.py`

Section 2.2 (lines ~60-75):
- `region.owner_faction_id != Faction.HERO_GUILD` — checks stored owner enum int
- `region.owner_faction_id != Faction.MONSTER_HORDE` — checks stored owner enum int
- `owner_faction_id_set=Faction.HERO_GUILD` / `Faction.MONSTER_HORDE` — sets owner (still int, out of scope to change type)

### Data Model Constraint
`WorldUpdate.owner_faction_id_set: Optional[int]` and `RegionState.owner_faction_id: Optional[int]` store Faction enum integer values. Changing this type is out of scope. The SET operations (conquest/liberation assignment) must still pass `Faction.MONSTER_HORDE` / `Faction.HERO_GUILD` integer values.

Only the COMPARISON operations (is this entity/region a hero/monster?) are being refactored.

## Mechanics/Engine Constraints

- `docs/mechanics/05_world_evolution.md` — influence conquest/liberation is a core mechanic
- No formula changes allowed (ticket constraint)

## Parity Ledger Overlap

- `world_dynamics.yaml` — entries for ownership transitions; behavior is preserved (same thresholds)

## Risks and Open Questions

**Entity side** (influence.py): `EntityIdentityResolver.resolve(entity)` → `faction_id` string → `is_protector()`/`is_invader()`. Legacy entities with only `identity.faction=Faction.HERO_GUILD` → fallback to `get_faction_id_str(entity)` → "hero_guild" → `is_protector()` returns True. Safe.

**Region owner side** (both files): `region.owner_faction_id` is `Optional[int]` (Faction enum int value). To use semantics service: convert via `Faction(val).name.lower()` → string faction_id → `is_invader()`/`is_protector()`. Safe for known enum values; `try/except ValueError` for unknown ints.

**`process_conquest_lifecycle`** checks `w_upd.owner_faction_id_set == Faction.MONSTER_HORDE` — this is comparing a freshly-written int value, NOT entity identity. Leave as-is (comparing authored data, not runtime entity identity).

## Anti-Drift Hazards

- Do not change `owner_faction_id_set` assignments — those must stay as Faction enum values
- Existing tests use `.value` for assertions (e.g., `== Faction.MONSTER_HORDE.value`) — preserve this behavior
