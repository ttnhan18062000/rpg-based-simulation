---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260609-FRONTIER-EXTENDED-PACK
phase: done
date: 2026-06-09
tags: [frontier, extended, pack]
---

# TCK-20260609-FRONTIER-EXTENDED-PACK

## Title
Add frontier_extended_pack as the first controlled horizontal content expansion

## Status
DONE

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
- [x] frontier_extended_pack manifest exists with valid format
- [x] Pack has at least one composition consuming it
- [x] Pack has at least one scenario consuming it
- [x] All archetypes in the pack are consumed by populations
- [x] All populations in the pack are consumed by modules or ecologies
- [x] All modules in the pack are consumed by a composition
- [x] Strict world matrix tests pass with new pack rows
- [x] Expansion gate passes after pack is added
- [x] No new vertical mechanism is introduced without a design ticket

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
- Added orc_territory biome (no hill terrain type exists — used plain)
- Two new populations: orc_clan_warband (orc_brute x5), sacred_grove_guardians (spirit_guardian x2)
- forest_warden_patrol already existed but had no module consumer — forest_warden_grove resolves this
- forest_warden_grove requires wolf_den_near_forest (grid adjacency: sacred_grove/deep_forest regions)
- frontier_extended composition excludes moon_cult_ruins to avoid CAT-REL-099 propagation
- Pack manifest lives in data/content/packs/ (not in CANONICAL_FAMILIES — purely metadata)
- All new catalog content uses STATE: ADDITIONAL (exempt from gate 04 active-data check)

## Test Summary
- test_strict_world_matrix.py: 28 passed, 45 xfailed (2 new rows fully pass pre-assembly tests)
- test_expansion_gate.py: 11 passed, 1 xfailed (gate 11 unchanged, CAT-REL-099)

## Files Changed
- data/content/world/biomes.yaml (append orc_territory)
- data/content/entities/populations.yaml (append orc_clan_warband, sacred_grove_guardians)
- data/content/world/ecologies.yaml (append orc_territory_ecology, sacred_grove_ecology)
- data/content/simulation_scenarios/frontier_scenarios.yaml (append 2 scenarios)
- tests/integration/content/test_strict_world_matrix.py (add 2 matrix rows)
- data/content/world_modules/orc_clan_territory.yaml (new)
- data/content/world_modules/forest_warden_grove.yaml (new)
- data/content/world_compositions/frontier_extended.yaml (new)
- data/content/packs/frontier_extended_pack.yaml (new)

## Completion Summary
First controlled horizontal expansion pack implemented. 3 previously-orphaned archetypes
(orc_brute, forest_ranger, spirit_guardian) now have complete consumer chains through
populations → ecologies → modules → composition → scenarios. Expansion gate: 11/12 pass
(gate 11 remains xfail, CAT-REL-099 pre-existing). No vertical mechanisms introduced.
