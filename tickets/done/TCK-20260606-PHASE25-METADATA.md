# TCK-20260606-PHASE25-METADATA

## Title

Preserve archetype metadata and validate population preferred spawn regions

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Preserve archetype and population metadata through compile/assembly boundaries and validate preferred spawn regions against the selected module/composition contributions.

## Scope

- Add archetype metadata fields to `ResolvedEntityProfile` in `src/worldassembly/models.py`.
- Populate archetype metadata in `CompileProfileResolver` (via `EntityArchetypeResolver`) during entity resolution.
- Validate preferred spawn regions against module-declared regions in `WorldAssemblyResolver.resolve_module_contribution`.
- Fix incorrect `FactionSemanticsService.resolve_faction_defaults` call (bug introduced during Phase 25 implementation) with correct `catalog_repo.get_faction` lookup.
- Add tests in `tests/unit/worldassembly/test_archetype_preservation.py`.

## Out of Scope

- None

## Acceptance Criteria

- [x] Population resolver outputs archetype IDs.
- [x] CompileContext keeps archetype/race/profile metadata.
- [x] World assembly uses archetype-native populations for new modules.
- [x] Legacy `role/faction/count` remains compatibility authoring.
- [x] Tests assert metadata survives resolution.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- `staging_artifacts/TCK-20260606-PHASE25-METADATA/`

## Related Code Areas

- `src/worldassembly/models.py`
- `src/worldassembly/resolver.py`
- `tests/unit/worldassembly/test_archetype_preservation.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- `ResolvedEntityProfile` was extended with: `archetype_id`, `race_id`, `role_id`, `faction_id`, `traits`, `themes`, `stat_profile_id`, `combat_profile_id`, `cognition_profile_id`, `drive_profile_id`, `need_profile_id`, `sense_profile_id`, `inventory_profile_id`, `skill_profile_id`.
- `CompileProfileResolver.resolve` uses `EntityArchetypeResolver` to look up the archetype if the entity key ends with a known archetype ID. Resolved metadata is stored in the `ResolvedEntityProfile`.
- `WorldAssemblyResolver.resolve_module_contribution` now validates preferred spawn regions from population recipes against the module's declared region IDs. Missing regions raise `ResolverError`.
- Bug fixed: line 670 originally called `self.profile_resolver.faction_semantics.resolve_faction_defaults(f_id)` which doesn't exist on `FactionSemanticsService`. Fixed to use `self.catalog_repo.get_faction(f_id)`.
- Tests were corrected to use actual archetype data (role=`raider`, faction=`goblin_warband`, need/sense profiles from goblin race), pass a large enough topology (200×200) for goblin_camp bounds, and normalize the `WorldModuleSpec` before passing it to `resolve_module_contribution`.

## Test Summary

- Tests run: `tests/unit/worldassembly/` (26 tests), `tests/unit/content/` (133 tests)
- Tests added: `tests/unit/worldassembly/test_archetype_preservation.py` (2 new tests)
- All 159 tests pass, no regressions.

## Files Changed

- `src/worldassembly/models.py` — added archetype metadata fields to `ResolvedEntityProfile`
- `src/worldassembly/resolver.py` — archetype metadata population in `CompileProfileResolver`, preferred spawn region validation in `resolve_module_contribution`, faction lookup bug fix
- `tests/unit/worldassembly/test_archetype_preservation.py` — new test file [NEW]

## Completion Summary

Phase 25 is complete. Archetype metadata now flows through the assembly pipeline from `EntityArchetypeResolver` into `ResolvedEntityProfile` inside `CompileContext`. Preferred spawn region validation ensures population recipes reference regions that actually exist in the assembling module's region scope.
