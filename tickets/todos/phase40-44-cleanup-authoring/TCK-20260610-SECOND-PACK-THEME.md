# TCK-20260610-SECOND-PACK-THEME

## Title
Select and document second content pack theme before implementation begins

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Phase 43.1. Before implementing the second content pack, one theme must be formally selected and its dependencies, reuse list, and scope boundaries documented. The plan recommends `swamp_border_pack` as the safest choice. This ticket confirms the selection, documents what existing foundation IDs it reuses and what new horizontal content it adds, and verifies Phase 43 entry criteria are met before implementation starts.

## Scope
- Verify Phase 43 entry criteria: Phase 34 pack contract passes, `frontier_extended_pack` manifest validates, `frontier_extended_pack` strict matrix passes, base-only strict matrix passes, base + first pack strict matrix passes, content source report distinguishes base and pack records, hardcoded fallback guard passes
- Select one theme: `swamp_border_pack` (recommended) or alternative from list
- Document in `stored_artifacts/TCK-20260610-SECOND-PACK-THEME/theme_selection.md`:
  - Selected theme ID
  - Existing foundation IDs reused (factions, races, materials, biomes)
  - New horizontal content to add (new factions/archetypes/scenarios scoped to swamp border)
  - Forbidden vertical systems this pack must NOT introduce
  - Pack dependencies on existing content

## Out of Scope
- Implementing any pack files (that is TCK-20260610-SWAMP-BORDER-PACK)
- Changing pack manifest schema

## Acceptance Criteria
- [ ] Phase 43 entry criteria verified (each one checked)
- [ ] One theme selected and documented
- [ ] Theme uses existing mechanisms (races, factions, archetypes, materials, resources, items, recipes, biomes, modules, scenarios, relationship models)
- [ ] Theme does not introduce forbidden vertical systems (diplomacy engine, weather, lineage, new combat engine, new pack schema)
- [ ] Clear module/composition/scenario consumer list documented
- [ ] Dependencies listed

## Related Tickets
- TCK-20260610-SWAMP-BORDER-PACK (implementation — depends on this)
- TCK-20260610-MULTI-PACK-INTERACTION (validation — depends on both packs)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `content_packs/` — existing pack structure for reference
- `data/content/` — foundation IDs to reuse

## Assumptions / Open Questions
- Are any lizardfolk/swamp race/faction IDs already in `data/content/`? Check before selecting theme.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
