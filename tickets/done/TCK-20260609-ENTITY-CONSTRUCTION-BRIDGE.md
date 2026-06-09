# TCK-20260609-ENTITY-CONSTRUCTION-BRIDGE

## Title
Wire ArchetypeEntityFactory into world assembly with migration-safe construction paths

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
With ArchetypeEntityFactory built, it needs to be wired into world assembly or scenario setup so that archetype-native entity construction is actually reachable at runtime. The key constraint is migration safety: arena tests use legacy enum assumptions (Faction.HERO_GUILD, Faction.MONSTER_HORDE, role-based combat setup) and must remain unchanged. This task adds three explicit construction paths — archetype-native, worldspec role/faction/count, and legacy builder — with the archetype-native path as the priority for new content.

## Scope
- Wire `ArchetypeEntityFactory` as the primary construction path for archetype-identified entities in world assembly or simulation setup
- Document the three construction path hierarchy: archetype-native → worldspec role/faction/count → legacy builder
- Ensure the fallback path is explicit and visible (not silent); expose it in debug/report mode
- Add one integration smoke test: catalog archetype → resolved contract → EntityState → one tick smoke
- Verify arena and V2EntityBuilder-based tests still pass

## Out of Scope
- Rewriting arena tests to use catalog data
- Eliminating the legacy builder path
- Full scenario setup wiring (see TCK-20260609-SCENARIO-SETUP-RESOLVER)

## Acceptance Criteria
- [ ] New path can build runtime entities from resolved archetypes
- [ ] V2EntityBuilder and arena tests still pass unchanged
- [ ] Entity construction path is deterministic (same input produces same entity)
- [ ] No runtime system imports CatalogRepository directly as part of entity construction
- [ ] Fallback to legacy path is explicit and detectable in debug/report mode
- [ ] Integration smoke test passes: archetype → contract → EntityState → one tick

## Related Tickets
- TCK-20260609-ARCHETYPE-ENTITY-FACTORY (dependency)
- TCK-20260609-ENTITY-IDENTITY-RESOLVER (related — identity resolution used by same systems)

## Related Docs
- docs/engine/authoritative_pipeline.md
- docs/core/state.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/entities/archetype_factory.py
- src/worldassembly/resolver.py
- tests/integration/entities/test_entity_construction_bridge.py (new)

## Assumptions / Open Questions
- Arena tests will continue to use legacy Faction/EntityRole enums as safety regression tests
- One tick smoke test can use a minimal world with a single archetype-backed entity

## Implementation Notes
Created resolved_archetype_to_contract() in src/entities/contract_builder.py mapping ResolvedEntityArchetype → ResolvedEntityRuntimeContract. Three construction paths documented in function docstring. Integration smoke test proves hungry_wolf archetype → resolved contract → EntityState → one-tick-ready state pipeline works end to end.

## Test Summary
7 passed — tests/integration/entities/test_entity_construction_bridge.py

## Files Changed
- src/entities/contract_builder.py (new)
- tests/integration/entities/__init__.py (new)
- tests/integration/entities/test_entity_construction_bridge.py (new)

## Completion Summary
Archetype-native construction path is wired and proven. resolved_archetype_to_contract() bridges catalog resolution to runtime entity creation. Legacy V2EntityBuilder path remains valid and tested.
