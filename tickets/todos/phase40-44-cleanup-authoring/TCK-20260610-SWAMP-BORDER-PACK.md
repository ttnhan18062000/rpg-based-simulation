# TCK-20260610-SWAMP-BORDER-PACK

## Title
Implement swamp_border_pack content pack with manifest, content files, and pack validation tests

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Phase 43.2. Implement the second content pack selected in TCK-20260610-SECOND-PACK-THEME using the Phase 34 pack manifest schema and validation pipeline. Pack must have at least one faction, one population, one module, one composition, and one scenario. All active records must have consumer paths. Pack can be disabled without affecting base world.

## Scope
- Create `content_packs/swamp_border_pack/manifest.yaml` following Phase 34 pack manifest schema
- Create required content directories and files:
  - `content_packs/swamp_border_pack/content/living/` (populations)
  - `content_packs/swamp_border_pack/content/social/` (factions, perspectives)
  - `content_packs/swamp_border_pack/content/entities/` (archetypes)
  - `content_packs/swamp_border_pack/content/world/` (biomes, terrain)
  - `content_packs/swamp_border_pack/content/world_modules/`
  - `content_packs/swamp_border_pack/content/world_compositions/`
  - `content_packs/swamp_border_pack/content/simulation_scenarios/`
- Add pack validation tests:
  - Pack manifest validates against Phase 34 schema
  - Pack dependencies resolve
  - All active pack data is reachable via catalog
  - Pack strict matrix passes
  - Pack disabled → base world unchanged

## Out of Scope
- Adding new pack infrastructure or manifest schema changes
- New vertical systems (no new diplomacy, weather, combat engine)
- Implementing new foundation concept types not already present in base

## Acceptance Criteria
- [ ] `content_packs/swamp_border_pack/manifest.yaml` exists and validates
- [ ] Pack has at least one faction
- [ ] Pack has at least one population
- [ ] Pack has at least one module
- [ ] Pack has at least one composition
- [ ] Pack has at least one scenario
- [ ] Pack dependencies resolve against base content
- [ ] Pack can be disabled without affecting base strict matrix
- [ ] Pack strict matrix passes when enabled
- [ ] All active records have consumer paths

## Related Tickets
- TCK-20260610-SECOND-PACK-THEME (prerequisite — theme selection)
- TCK-20260610-MULTI-PACK-INTERACTION (validation — requires this pack)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `content_packs/` — sibling packs for reference
- `src/content/repository.py` — pack loading
- `src/content/pack_validator.py` or equivalent — manifest validation

## Assumptions / Open Questions
- Theme selection from TCK-20260610-SECOND-PACK-THEME must be DONE before starting implementation.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
