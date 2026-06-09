# TCK-20260609-ARCHETYPE-ENTITY-FACTORY

## Title
Implement ArchetypeEntityFactory — convert ResolvedEntityRuntimeContract into EntityState

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Once ResolvedEntityRuntimeContract exists, the simulation needs a factory that creates a real EntityState from it. Currently V2EntityBuilder is the only entity construction path and it knows nothing about catalog archetypes. ArchetypeEntityFactory fills this gap: it accepts a contract plus an EntitySpawnContext (position, region, alive, active, tick, name override) and produces a valid EntityState. The first version must be conservative — unresolved profile IDs go into metadata rather than being silently dropped.

## Scope
- Create `ArchetypeEntityFactory` with `build_entity(entity_id, contract, spawn) -> EntityState` in `src/entities/archetype_factory.py`
- Create `EntitySpawnContext` dataclass/model with fields: position, spawn_region, initial_alive, initial_active, current_tick (optional), name_override (optional)
- Map contract fields to EntityState: identity (role, faction, kind, archetype_id, race_id), combat (hp, max_hp, atk, def_stat, attack_range, readiness, alive), inventory (items, gold), unresolved profile IDs stored in identity extension/metadata
- Add `tests/unit/entities/test_archetype_entity_factory.py` with test cases: build human worker, build wolf, build goblin raider, build boss-like entity without boss class, factory does not require enemy_type field

## Out of Scope
- Replacing V2EntityBuilder — it remains valid for legacy tests
- Forcing all profile IDs into active runtime behavior immediately
- Modifying world assembly pipeline (see TCK-20260609-ENTITY-CONSTRUCTION-BRIDGE)

## Acceptance Criteria
- [ ] ArchetypeEntityFactory.build_entity creates a valid EntityState
- [ ] Combat values on resulting EntityState match the contract
- [ ] Inventory values on resulting EntityState match the contract
- [ ] archetype_id and race_id are preserved in identity or metadata
- [ ] Legacy role/faction projection is applied where EntityState fields require it
- [ ] Boss-like archetype builds successfully without special boss logic
- [ ] Animal archetype builds successfully without monster-specific source truth
- [ ] V2EntityBuilder-based tests still pass unchanged
- [ ] Factory does not import CatalogRepository

## Related Tickets
- TCK-20260609-ENTITY-RUNTIME-CONTRACT (dependency — must be done first)
- TCK-20260609-ENTITY-CONSTRUCTION-BRIDGE (successor)

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/core/entities.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/entities/archetype_factory.py (new)
- src/entities/runtime_contract.py
- src/core/state.py (EntityState)
- tests/unit/entities/test_archetype_entity_factory.py (new)

## Assumptions / Open Questions
- EntityState can accept archetype_id / race_id in identity metadata without breaking existing arena tests
- Unresolved profile IDs stored as strings in identity extension do not affect combat or movement behavior

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
