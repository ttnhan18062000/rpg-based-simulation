# TCK-20260609-ENTITY-RUNTIME-CONTRACT

## Title
Define ResolvedEntityRuntimeContract — boundary model between catalog resolution and entity creation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The simulation has resolved archetype data (ResolvedEntityArchetype, ResolvedPopulation, CompileContext, ResolvedModuleContribution) but no typed contract governing exactly what a resolved archetype must provide before it becomes a runtime entity. Without this contract, EntityState construction couples directly to catalog internals. This task creates ResolvedEntityRuntimeContract as the explicit boundary: a frozen, serializable model carrying all runtime-relevant fields from identity through combat stats, inventory, and profile source IDs.

## Scope
- Create `ResolvedEntityRuntimeContract` as a frozen Pydantic BaseModel (or frozen dataclass) with fields: archetype_id, race_id, faction_id, role_id, profession_id, kind, legacy_role, legacy_faction, hp, max_hp, atk, def_stat, attack_range, readiness, inventory_items, starting_gold, traits, themes, cognition_profile_id, drive_profile_id, need_profile_id, sense_profile_id, skill_profile_id
- Place in `src/entities/runtime_contract.py` (or appropriate entities module)
- Add `tests/unit/entities/test_resolved_entity_runtime_contract.py` with tests for: contract construction, JSON serialization, that no repository/catalog imports are present, that legacy role/faction are optional projection fields only

## Out of Scope
- Implementing the factory that consumes the contract (see TCK-20260609-ARCHETYPE-ENTITY-FACTORY)
- Wiring into world assembly pipeline
- Modifying EntityState itself

## Acceptance Criteria
- [ ] ResolvedEntityRuntimeContract exists with all specified fields
- [ ] Contract includes clean identity: archetype_id, race_id, faction_id, role_id
- [ ] Contract includes legacy_role and legacy_faction only as optional projection fields
- [ ] Contract includes runtime combat values: hp, max_hp, atk, def_stat, attack_range, readiness
- [ ] Contract includes inventory_items dict and starting_gold
- [ ] Contract includes profile source IDs as optional strings
- [ ] Contract is serializable to JSON (model_dump / dataclass asdict)
- [ ] Contract module does not import CatalogRepository or any catalog loader
- [ ] Contract does not include enemy/ally source-truth fields
- [ ] Unit tests pass covering construction and serialization

## Related Tickets
- TCK-20260609-ARCHETYPE-ENTITY-FACTORY (successor — consumes this contract)
- TCK-20260609-ENTITY-CONSTRUCTION-BRIDGE (successor — wires the factory)

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/core/entities.md
- docs/core/attributes_and_classes.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/entities/runtime_contract.py (new)
- src/core/enums.py (EntityRole, Faction)
- tests/unit/entities/test_resolved_entity_runtime_contract.py (new)

## Assumptions / Open Questions
- ResolvedEntityArchetype and related resolved types already exist from phases 20–28
- The contract uses string IDs for profile references (not resolved profile objects) to stay decoupled

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
