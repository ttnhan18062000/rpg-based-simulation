---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260610-SECOND-PACK-THEME
phase: done
date: 2026-06-10
tags: [second, pack, theme]
---

# TCK-20260610-SECOND-PACK-THEME

## Title
Select and document second content pack theme before implementation begins

## Status
DONE

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
- [x] Phase 43 entry criteria verified (each one checked)
- [x] One theme selected and documented
- [x] Theme uses existing mechanisms (races, factions, archetypes, materials, resources, items, recipes, biomes, modules, scenarios, relationship models)
- [x] Theme does not introduce forbidden vertical systems (diplomacy engine, weather, lineage, new combat engine, new pack schema)
- [x] Clear module/composition/scenario consumer list documented
- [x] Dependencies listed

## Related Tickets
- TCK-20260610-SWAMP-BORDER-PACK (implementation — depends on this)
- TCK-20260610-MULTI-PACK-INTERACTION (validation — depends on both packs)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `data/content/packs/frontier_extended_pack.yaml` — reference for pack structure
- `data/content/social/factions.yaml` — swamp_tribe faction
- `data/content/living/races.yaml` — lizardfolk race
- `data/content/world/biomes.yaml` — sunken_swamp biome

## Assumptions / Open Questions
- lizardfolk race confirmed present; swamp_tribe faction confirmed present; sunken_swamp biome confirmed present

## Implementation Notes
Phase 43 entry criteria verified: 85 tests pass across test_strict_world_matrix, test_catalog_fallback, test_registry_bootstrap_modes. swamp_border_pack selected — lizardfolk, swamp_tribe, sunken_swamp, swamp terrain all exist in base catalog. New content: 3 archetypes (lizardfolk_scout, lizardfolk_shaman, swamp_troll), 2 populations, 1 world module, 1 scenario, 1 composition.

## Test Summary
No new tests — this is a planning/documentation ticket. Phase 43 entry criteria verified via existing test suite (85 tests pass).

## Files Changed
- `stored_artifacts/TCK-20260610-SECOND-PACK-THEME/theme_selection.md` (new)

## Completion Summary
swamp_border_pack selected as second content pack theme. Full foundation already in base catalog (race, faction, biome, terrain). Entry criteria verified. Theme selection document written to stored_artifacts. Ready for TCK-20260610-SWAMP-BORDER-PACK implementation.
