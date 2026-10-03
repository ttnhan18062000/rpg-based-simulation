---
ticket_id: TCK-20260630-WORLD-QUEST-LOCATION
phase: investigation
---

# Investigation: Quest required_location_tags vs Region IDs

## Code Path: Module Region → RegionSpec → Quest Validation

```
WorldModuleSpec.regions: List[RegionRecipeSpec]       (loaded from YAML)
  ↓  WorldModuleAuthoringNormalizer.normalize()
NormalizedWorldModule.regions: List[RegionRecipeSpec]  (unchanged, just copied)
  ↓  WorldAssemblyResolver.resolve_module_contribution() → line 778-784
RegionSpec(id=f"{prefix}{reg.id}", type=reg.type, bounds=reg.grid_bounds, ...)
  ↓  WorldAssemblyResolver.assemble() → merged into regions dict
WorldSpec.regions: List[RegionSpec]                    (keyed by region.id in compiler)
  ↓  WorldCompiler.compile() → line 354-360
"if loc_tag not in regions"  (regions is dict keyed by region.id)  ← BUG
```

## The Bug (compiler.py:354-360)

```python
for loc_tag in q_def.required_location_tags:
    if loc_tag not in regions:          # regions keyed by region.id e.g. "hometown"
        warnings.append(...)            # loc_tag = "plain" → never in {"hometown": ...}
```

`regions` is `Dict[str, RegionSpec]` keyed by `region.id` (e.g., `hometown`, `bandit_road`).
Quest tags like `plain`, `wilderness`, `mine` are terrain-role descriptors, never region IDs.
Result: 100% of location-tagged quests warn.

## RegionSpec Field Analysis

Current `RegionSpec` (schema.py:27-43):
- `id: str` — unique identifier (e.g., "hometown")
- `type: str` — ecological/atmospheric type (e.g., "town", "wilderness", "road")
- `bounds: tuple[int,int,int,int]`
- `terrain: Optional[str]` — GRASS, plain, forest, cave, etc. (physical surface)
- `hazard_level: Optional[float]`
- NO `tags` field

Current `RegionRecipeSpec` (recipe.py:11-27):
- Same fields as above using `grid_bounds` instead of `bounds`
- Has `extra="forbid"` — adding unknown keys to YAML would error
- NO `tags` field

## RegionSpec.type Values in Use

Surveyed from all modules:
- `"town"` — settled area (hometown regions)
- `"wilderness"` — open/hostile terrain (most non-settlement regions)
- `"road"` — path/trade-route regions (bandit_road in bandit_road_trade_pressure)

The `type` field covers coarse categories. Subtypes like `mine`, `ruins`, `cave`, `forest`, `mountain`, `plain`, `settlement`, `trade_route` cannot be expressed by `type` alone → need explicit `tags`.

## Quest Tag vs Region Type Mapping

| Quest needs     | Region type    | Matches after fix? | Tags needed        |
|-----------------|----------------|--------------------|--------------------|
| plain           | town           | NO                 | tags: [plain, ...]  |
| settlement      | town           | NO                 | tags: [settlement] |
| trade_route     | town           | NO                 | tags: [trade_route]|
| wilderness      | wilderness     | YES (type match)   | none               |
| road            | road           | YES (type match)   | none               |
| forest          | wilderness     | NO                 | tags: [forest]     |
| mine            | wilderness     | NO                 | tags: [mine]       |
| underground     | wilderness     | NO                 | tags: [underground]|
| cave            | wilderness     | NO                 | tags: [cave]       |
| ruins           | wilderness     | NO                 | tags: [ruins]      |
| mountain        | wilderness     | NO                 | tags: [mountain]   |
| plain (on wild) | wilderness     | NO                 | tags: [plain]      |

## Modules Requiring YAML Tag Updates

| Module                     | Region            | Current type | Tags to add             |
|----------------------------|-------------------|--------------|-------------------------|
| frontier_village_core      | hometown          | town         | [plain, settlement]     |
| trading_company_hub        | hometown          | town         | [plain, trade_route]    |
| old_mine_resource_loop     | old_mine          | wilderness   | [mine, underground]     |
| ruins_mystery_quest        | haunted_battlefield | wilderness | [ruins]                 |
| undead_battlefield         | haunted_battlefield | wilderness | [ruins]                 |
| goblin_camp_conflict       | goblin_camp       | wilderness   | [forest]                |
| scalable_bandit_camp       | bandit_road       | wilderness   | [forest]                |
| bandit_road_trade_pressure | bandit_road       | road         | [wilderness]            |
| moon_cult_ruins            | moon_cave         | wilderness   | [cave]                  |
| mountain_pass              | mountain_pass_zone | wilderness  | [mountain]              |
| nomadic_herd               | near_forest       | wilderness   | [plain]                 |
| forest_warden_grove        | sacred_grove      | wilderness   | [forest]                |
| forest_warden_grove        | deep_forest       | wilderness   | [forest]                |
| wolf_den_near_forest       | near_forest       | wilderness   | [forest]                |
| wolf_den_near_forest       | wolf_den          | wilderness   | [forest]                |

## Modules That Auto-Resolve (no YAML changes needed)

- `forest_deep_ecology`: no regions; quest needs `wilderness`. After fix, ANY `wilderness`-type region in the assembled world satisfies this. wilderness_survival includes wolf_den_near_forest (type: wilderness) → satisfied.

## Stale Compile Reports

The existing compile reports are STALE — they were generated before quest_definitions were added to wolf_den_near_forest, undead_battlefield, scalable_bandit_camp, and other modules. After reimplementation:
- dungeon_crawl, urban_political, wilderness_survival, generated_frontier_3_42 must all be recompiled
- Target: zero quest location warnings in all reports

## Normalizer Impact

`WorldModuleAuthoringNormalizer.normalize()` (normalizer.py:133-157) copies `spec.regions` directly as `List[RegionRecipeSpec]`. When `RegionRecipeSpec` gains `tags`, no normalizer changes are needed — the tags travel automatically.

## Resolver Impact

`resolve_module_contribution()` (resolver.py:778-784) constructs `RegionSpec` from `RegionRecipeSpec`. This is where `tags` must be propagated:

```python
# Current (missing tags):
RegionSpec(id=f"{prefix}{reg.id}", type=reg.type, bounds=reg.grid_bounds,
           terrain=reg.terrain, hazard_level=reg.hazard_level)

# Fixed (add tags):
RegionSpec(id=f"{prefix}{reg.id}", type=reg.type, bounds=reg.grid_bounds,
           terrain=reg.terrain, hazard_level=reg.hazard_level, tags=list(reg.tags))
```

Also `WorldAssemblyValidator.validate()` (resolver.py:100-102) builds a dummy `RegionSpec` for per-module validation — must also propagate tags.

## Architecture Safety

- `tags: List[str]` on `RegionSpec` is metadata for quest routing. It does not mutate durable gameplay state — it is read-only during the compile validation pass.
- `RegionSpec` is frozen/immutable after construction; `Field(default_factory=list)` with frozen is safe.
- Existing worlds compiled without `tags` still work — defaults to `[]`.
