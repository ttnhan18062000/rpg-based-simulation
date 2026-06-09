# TCK-20260609-FRONTIER-EXTENDED-PACK

## Title
Add frontier_extended_pack as the first controlled horizontal content expansion

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
After the content expansion gate passes and the pack format is defined, the first horizontal expansion pack can be added. frontier_extended_pack is the recommended first pack: it may include orc clan, bandit route, dwarven mine, undead battlefield, forest wardens, merchant caravan, and moon cult ruin content. Every archetype must be consumed by a population, every population by a module/ecology, and every module by a composition. No new vertical mechanism may be introduced silently — pack must pass strict gate before merge.

## Scope
- Create `data/content/packs/frontier_extended_pack/` with pack manifest, content YAML files for included content
- Include at least one composition and one scenario consuming the pack
- Add one matrix row per included module to the strict world matrix (not one test per record)
- All archetypes consumed by populations, all populations by modules/ecologies, all modules by composition
- Pack must pass the expansion gate (TCK-20260609-CONTENT-EXPANSION-GATE) before commit

## Out of Scope
- Adding dragon/volcanic/frozen/swamp content unless each has a consuming module/scenario
- Introducing new vertical mechanisms (new gameplay behaviors, new combat systems)
- Adding content that does not have a population consumer

## Acceptance Criteria
- [ ] frontier_extended_pack manifest exists with valid format
- [ ] Pack has at least one composition consuming it
- [ ] Pack has at least one scenario consuming it
- [ ] All archetypes in the pack are consumed by populations
- [ ] All populations in the pack are consumed by modules or ecologies
- [ ] All modules in the pack are consumed by a composition
- [ ] Strict world matrix tests pass with new pack rows
- [ ] Expansion gate passes after pack is added
- [ ] No new vertical mechanism is introduced without a design ticket

## Related Tickets
- TCK-20260609-CONTENT-EXPANSION-GATE (dependency — gate must pass first)
- TCK-20260609-CONTENT-PACK-FORMAT (dependency — pack format must exist)
- TCK-20260609-STRICT-WORLD-MATRIX (related — new matrix rows added here)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
None.

## Related Code Areas
- data/content/packs/frontier_extended_pack/ (new)
- tests/integration/content/test_strict_world_matrix.py (extend with new rows)

## Assumptions / Open Questions
- Moon cult ruin content already partially exists; pack may reference or extend it
- Do not add more than 6-8 archetypes in the first pack to keep the scope manageable

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
