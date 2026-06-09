# TCK-20260609-MIGRATION-MAP-YAML

## Title
Create machine-readable migration map YAML tracking legacy-to-catalog content migration

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Runtime mode enforcement and the hardcoded gameplay guard both need a machine-readable record of which legacy IDs are known, how they map to catalog equivalents, and whether fallback is still allowed. Without this map, any static scan would need to either allow all legacy IDs (too permissive) or reject them all (breaks existing behavior). This task creates data/content/compatibility/migration_map.yaml with entries covering items, recipes, regions, services, legacy enemies, legacy factions, and legacy roles.

## Scope
- Create `data/content/compatibility/migration_map.yaml` with entries for required families: items, recipes, regions, services, legacy enemies, legacy factions, legacy roles
- Each entry must include: legacy_id, legacy_family, catalog_family, catalog_id, adapter, status, fallback_allowed, notes
- Statuses: catalog_authoritative, compat_projected, fallback_only, deprecated, removed
- Populate with all currently hardcoded legacy gameplay IDs in the codebase (scan src/ fallback maps)
- Add a schema validation test or loader that rejects migration_map.yaml entries with missing required fields

## Out of Scope
- Implementing the guard that uses this map (see TCK-20260609-HARDCODED-GAMEPLAY-GUARD)
- Migrating content records to catalog (this is a tracking file, not a migration)
- Adding entries for content not currently hardcoded anywhere

## Acceptance Criteria
- [ ] data/content/compatibility/migration_map.yaml exists
- [ ] Items family entries are present
- [ ] Recipes family entries are present
- [ ] Regions family entries are present
- [ ] Services family entries are present
- [ ] Legacy enemies are mapped to archetypes or compatibility projections
- [ ] Legacy factions and roles are mapped to clean IDs where available
- [ ] All required fields (legacy_id, legacy_family, catalog_family, catalog_id, adapter, status, fallback_allowed) are present per entry
- [ ] A loader or validator test ensures the YAML schema is correct

## Related Tickets
- TCK-20260609-HARDCODED-GAMEPLAY-GUARD (successor — uses this map)
- TCK-20260609-REGISTRY-BOOTSTRAP-MODES (related — bootstrap reads fallback_allowed)

## Related Docs
- docs/engine/known_limitations.md

## Related Stored Artifacts
None.

## Related Code Areas
- data/content/compatibility/migration_map.yaml (new)
- src/content/repository.py (scan for hardcoded IDs)
- src/core/registries.py (scan for hardcoded IDs)
- tests/unit/content/test_migration_map_schema.py (new)

## Assumptions / Open Questions
- Not all legacy IDs are currently tracked anywhere; scan of src/ fallback maps needed during implementation

## Implementation Notes
Scanned src/core/registries.py, src/worldassembly/resolver.py, src/entities/identity_resolver.py, and data/content/compatibility/legacy_enemy_projection.yaml to enumerate all hardcoded legacy IDs. Created 30 entries across 8 families. Key decisions: deprecated items (no consumers found by active-data-consumer gate), compat_projected for resource/recipe/region/role/faction/enemy fallbacks, catalog_authoritative for services whose IDs are unchanged.

## Test Summary
10/10 unit tests pass in tests/unit/content/test_migration_map_schema.py. Tests cover: file existence, schema_version header, entry count, required fields, valid statuses, known families, boolean fallback_allowed, uniqueness, family coverage, and deprecated notes.

## Files Changed
- data/content/compatibility/migration_map.yaml (new — 30 entries, 8 families)
- tests/unit/content/test_migration_map_schema.py (new — 10 schema validation tests)

## Completion Summary
All acceptance criteria met. migration_map.yaml created and validated. Successor tickets TCK-20260609-HARDCODED-GAMEPLAY-GUARD and TCK-20260609-REGISTRY-BOOTSTRAP-MODES can now consume this file.
