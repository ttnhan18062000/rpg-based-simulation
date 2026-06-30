---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260630-WORLD-QUEST-LOCATION
phase: open
date: 2026-06-30
tags: [world, quests, compiler, bug]
---

# TCK-20260630-WORLD-QUEST-LOCATION

## Title
Fix quest required_location_tags matching against region type instead of region id

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
`required_location_tags` in quest definitions use terrain/role descriptors (`plain`,
`settlement`, `road`, `wilderness`, `mine`, `cave`, `forest`) but the WorldCompiler
validates them against region `id` values (like `hometown`, `bandit_road`). These
never match. Every location-tagged quest in every world produces a compile warning,
meaning location-based quest routing is silently broken for 100% of quests that
use it. 4/5 compiled worlds have this warning; only `sandbox_world` (0 quests) is clean.

## Scope
1. In `src/worldbuilding/compiler.py` (~line 354): change the validation to match
   `required_location_tags` against region `type` field values instead of region `id` keys.
   The region spec has `type: town|wilderness|settlement|...` which maps to the tag vocabulary.
2. Add a region `tags: List[str]` field to `RegionSpec` in `src/worldbuilding/schema.py` so
   modules can opt-in to richer semantic tagging beyond `type` (e.g., `mine`, `underground`,
   `cave` — subtypes not representable by the `type` enum alone).
3. Update compiler quest validation to match `loc_tag` against: `region.type` OR
   any entry in `region.tags`. Either match is sufficient to satisfy the tag.
4. Update the `world_module_spec` region format in `src/worldmodules/schema.py` to
   include `tags: List[str]` at the region spec level (matching worldbuilding schema).
5. Re-author affected module region entries to include explicit `tags` where `type` alone
   is insufficient (e.g., `old_mine_resource_loop` region needs `tags: [mine, underground]`).
6. Re-compile all worlds and confirm zero quest location warnings.
7. Update parity ledger entry in `docs/parity_ledger/substrate.yaml` if one covers quest
   routing.

## Out of Scope
- Changing the adventure routing system (P0-A feature gate)
- Adding new quests or changing quest content
- Changing quest reward or encounter logic

## Acceptance Criteria
- [ ] `data/worlds/dungeon_crawl/world_compile_report.json` has zero warnings
- [ ] `data/worlds/urban_political/world_compile_report.json` has zero warnings
- [ ] `data/worlds/wilderness_survival/world_compile_report.json` has zero warnings
- [ ] `data/worlds/generated_frontier_3_42/world_compile_report.json` has zero warnings
- [ ] `RegionSpec` in `src/worldbuilding/schema.py` has `tags: List[str]` field
- [ ] `WorldModuleSpec` region format has `tags: List[str]` field
- [ ] `pytest tests/integration/worldassembly/` passes (no regressions)
- [ ] At least one test verifies that `required_location_tag: plain` matches a region
      with `type: town` or `tags: [plain]`

## Related Tickets
- TCK-20260630-WORLD-DEPLOY-MODULES (compile all worlds after this fix)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md` — region topology spec
- `docs/engine/kernel.md` — quest routing at packetization phase

## Related Stored Artifacts
- None yet

## Related Code Areas
- `src/worldbuilding/compiler.py:354-362` — quest location tag validation
- `src/worldbuilding/schema.py` — `RegionSpec`, `QuestDefinitionSpec`
- `src/worldmodules/schema.py` — module region schema
- `data/content/world_modules/old_mine_resource_loop.yaml` — needs `tags: [mine, underground]`
- `data/content/world_modules/frontier_village_core.yaml` — needs `tags: [plain, settlement]`
- `data/content/world_modules/goblin_camp_conflict.yaml` — needs `tags: [wilderness, forest]`
- All modules with quest_definitions: bandit_road_trade_pressure, forest_deep_ecology,
  forest_warden_grove, goblin_camp_conflict, moon_cult_ruins, mountain_pass, nomadic_herd,
  old_mine_resource_loop, ruins_mystery_quest

## Assumptions / Open Questions
- Is `type` always sufficient (e.g., does any tag need both `type` AND a subtype)?
  `mine` and `underground` are not valid `type` values → they need explicit `tags`.
- If `tags` is added to `RegionSpec` in worldbuilding schema, must also ensure
  `WorldModuleAuthoringNormalizer` preserves `tags` during normalization.
- Check `docs/parity_ledger/substrate.yaml` — if quest routing has a P0 entry, update it.

## Implementation Notes
- The bug: `src/worldbuilding/compiler.py:355-358` iterates `required_location_tags`
  and checks `if loc_tag not in regions` — where `regions` is keyed by `region.id`.
  Fix: build a parallel mapping of `region.type → [region_ids]` and check tag against
  `{r.type for r in regions.values()} | {t for r in regions.values() for t in r.tags}`.
- Do NOT change the region `id` — these are stable references used by resources and buildings.
- Module region current shape: `{id, type, grid_bounds, terrain, hazard_level}`. Add `tags: []`.

## Test Summary
- Unit test: `test_quest_location_tag_matches_region_type` — compile a minimal world
  where quest tags are region types, assert 0 warnings
- Unit test: `test_quest_location_tag_matches_region_explicit_tag` — region has
  `tags: [mine, underground]`, quest needs `mine`, assert passes
- Unit test: `test_quest_location_tag_warns_on_no_match` — ensure warning still fires
  when genuinely no match exists (regression guard)
- Integration: `pytest tests/integration/worldassembly/` — all pass, zero warnings
  in all compiled world reports

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
