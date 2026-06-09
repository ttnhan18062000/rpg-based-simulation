# TCK-20260609-ENTITY-IDENTITY-RESOLVER

## Title
Add EntityIdentityResolver with clean-first fallback to legacy enum identity

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Runtime systems (combat, quests, region threat classification) currently inspect legacy Faction/EntityRole enum fields directly on EntityState. As the system moves toward clean catalog identity (archetype_id, race_id, faction_id, role_id strings), a resolver layer is needed that reads clean identity first and falls back to legacy enums only when necessary. EntityIdentityResolver resolves a ResolvedEntityIdentity from any EntityState regardless of how it was constructed, and exposes a source field indicating which path was used. This must exist before high-impact systems start using relation projection.

## Scope
- Create `EntityIdentityResolver` in `src/entities/identity_resolver.py` with `resolve(entity: EntityState) -> ResolvedEntityIdentity`
- Create `ResolvedEntityIdentity` model with: entity_id, archetype_id (optional), race_id (optional), faction_id, role_id, profession_id (optional), legacy_faction (optional), legacy_role (optional), source literal: clean_metadata | runtime_identity_extension | compatibility_projection | legacy_enum
- Resolution order: clean archetype/race/faction/role metadata → runtime identity extension → compatibility projection → legacy enum fields
- Fail clearly on missing identity unless runtime mode allows unknown (TEST_MANUAL)
- Add `tests/unit/entities/test_entity_identity_resolver.py` with cases: clean archetype resolves clean identity, legacy-only arena entity resolves via legacy enum, mixed prefers clean, missing faction/role fails clearly, resolver does not import CatalogRepository

## Out of Scope
- Modifying EntityState structure
- Rewriting arena tests
- Wiring resolver into combat/quest systems in this ticket (that is follow-on work)

## Acceptance Criteria
- [ ] EntityIdentityResolver.resolve() returns ResolvedEntityIdentity
- [ ] Clean archetype/race/faction/role IDs are read when present in entity metadata
- [ ] Legacy enum-backed entities still resolve via legacy_enum source
- [ ] Clean identity wins when both clean and legacy identity exist
- [ ] Missing faction/role produces a clear failure (or explicit unknown result in TEST_MANUAL mode)
- [ ] source field correctly reflects resolution path used
- [ ] Resolver does not import CatalogRepository
- [ ] V2EntityBuilder and arena tests still pass unchanged

## Related Tickets
- TCK-20260609-ENTITY-RUNTIME-CONTRACT (related — contract defines the clean identity fields)
- TCK-20260609-ENTITY-CONSTRUCTION-BRIDGE (related — factory sets the clean metadata this resolver reads)

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/core/entities.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/entities/identity_resolver.py (new)
- src/core/state.py (EntityState)
- src/core/enums.py (EntityRole, Faction)
- tests/unit/entities/test_entity_identity_resolver.py (new)

## Assumptions / Open Questions
- EntityState already carries some form of metadata dict where archetype_id/race_id/faction_id strings can be stored (set by ArchetypeEntityFactory)
- RuntimeContentMode is accessible for the missing-identity failure behavior (TEST_MANUAL allows unknown)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
