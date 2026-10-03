---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260630-WORLD-QUEST-LOCATION
phase: done
date: 2026-06-30
tags: [world, quests, compiler, bug]
---

# TCK-20260630-WORLD-QUEST-LOCATION

## Title
Fix quest required_location_tags matching against region type instead of region id

## Status
DONE

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
- `src/worldbuilding/schema.py` — added `tags: List[str] = Field(default_factory=list)` to `RegionSpec`
- `src/worldbuilding/recipe.py` — added `tags: List[str]` to `RegionRecipeSpec`; added `List` to imports; propagated `tags` in `WorldTemplateExpander.expand()`
- `src/worldbuilding/compiler.py` — replaced region-ID lookup with `tag_pool` built from `spec.regions[*].type + spec.regions[*].tags`; updated warning message text
- `src/worldassembly/resolver.py` — propagated `tags` in `resolve_module_contribution()` RegionSpec construction; propagated `tags` in `WorldAssemblyValidator` dummy spec
- `data/content/world_modules/frontier_village_core.yaml` — hometown: tags [plain, settlement]
- `data/content/world_modules/trading_company_hub.yaml` — hometown: tags [plain, trade_route]
- `data/content/world_modules/old_mine_resource_loop.yaml` — old_mine: tags [mine, underground]
- `data/content/world_modules/ruins_mystery_quest.yaml` — haunted_battlefield: tags [ruins]
- `data/content/world_modules/undead_battlefield.yaml` — haunted_battlefield: tags [ruins]
- `data/content/world_modules/goblin_camp_conflict.yaml` — goblin_camp: tags [forest]
- `data/content/world_modules/scalable_bandit_camp.yaml` — bandit_road: tags [forest]
- `data/content/world_modules/bandit_road_trade_pressure.yaml` — bandit_road: tags [wilderness]
- `data/content/world_modules/moon_cult_ruins.yaml` — moon_cave: tags [cave]
- `data/content/world_modules/mountain_pass.yaml` — mountain_pass_zone: tags [mountain]
- `data/content/world_modules/nomadic_herd.yaml` — near_forest: tags [plain]
- `data/content/world_modules/forest_warden_grove.yaml` — sacred_grove, deep_forest: tags [forest]
- `data/content/world_modules/wolf_den_near_forest.yaml` — near_forest, wolf_den: tags [forest]
- `tests/unit/worldbuilding/test_world_compiler.py` — added 3 new tests; fixed base spec quest tag to use `"wilderness"` (region type) instead of `"wilds"` (region ID)
- `docs/parity_ledger/substrate.yaml` — updated SUBSTRATE-NEW-007 to reflect type+tags validation
- `data/worlds/{dungeon_crawl,urban_political,wilderness_survival,generated_frontier_3_42}/` — resolved and recompiled; zero quest location warnings
- `staging_artifacts/TCK-20260630-WORLD-QUEST-LOCATION/` — investigation.md, test_plan.md, plan.md

## Completion Summary
Fixed the WorldCompiler's quest location validation: replaced the broken check that compared `required_location_tags` against region `id` keys with a semantic tag pool built from each region's `type` field plus a new explicit `tags: List[str]` field. Added `tags` to both `RegionSpec` (schema.py) and `RegionRecipeSpec` (recipe.py), propagated tags through the assembly resolver, and annotated 15 module region entries across 13 YAML files so that subtypes like `mine`, `ruins`, `forest`, `settlement`, `cave`, `mountain`, `trade_route`, and `plain` are reachable. All four compiled worlds now report zero quest location warnings (was 4–18 warnings each). Tests: 141 pass (98 unit + 43 integration), 3 new compiler tests added.
