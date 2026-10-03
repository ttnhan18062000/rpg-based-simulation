---
ticket_id: TCK-20260630-WORLD-QUEST-LOCATION
phase: plan
---

# Implementation Plan

## Step 1: Add `tags` to `RegionSpec` (src/worldbuilding/schema.py)

Add after `hazard_level` field:
```python
tags: List[str] = Field(default_factory=list, description="Semantic labels for quest routing (e.g. mine, forest, ruins)")
```
`RegionSpec` is frozen=True; `Field(default_factory=list)` is safe with frozen models.

## Step 2: Add `tags` to `RegionRecipeSpec` (src/worldbuilding/recipe.py)

Same field after `hazard_level`:
```python
tags: List[str] = Field(default_factory=list, description="Semantic labels for quest routing")
```
`RegionRecipeSpec` has `extra="forbid"` — adding this as an explicit field allows YAML authors to use it. Existing YAMLs without `tags` get `[]` by default.

## Step 3: Propagate `tags` in the Assembly Resolver (src/worldassembly/resolver.py)

**3a. resolve_module_contribution() ~line 778-784:**
Add `tags=list(getattr(reg, 'tags', []))` to the `RegionSpec()` constructor call.

**3b. WorldAssemblyValidator.validate() ~line 100-102:**
The dummy WorldSpec build also constructs `RegionSpec` — add `tags=list(r.tags)` there.

## Step 4: Fix Compiler Quest Validation (src/worldbuilding/compiler.py:354-362)

Replace:
```python
for loc_tag in q_def.required_location_tags:
    if loc_tag not in regions:
        warnings.append(
            f"QuestDefinition '{qid}' required_location_tag '{loc_tag}' "
            f"does not match any region ID in this world"
        )
```
With:
```python
# Build lookup: semantic tag value → True if any region carries it
tag_pool: set[str] = set()
for r in regions.values():
    if r.type:
        tag_pool.add(r.type)
    for t in getattr(r, 'tags', []):
        tag_pool.add(t)

for loc_tag in q_def.required_location_tags:
    if loc_tag not in tag_pool:
        warnings.append(
            f"QuestDefinition '{qid}' required_location_tag '{loc_tag}' "
            f"does not match any region type or tag in this world"
        )
```
Note: `tag_pool` is built once per compile pass (outside the per-quest loop), not per-quest.

## Step 5: Update Module YAMLs

Add `tags:` field to regions in 15 locations across 13 modules:

| Module file | Region id | tags to add |
|---|---|---|
| frontier_village_core.yaml | hometown | [plain, settlement] |
| trading_company_hub.yaml | hometown | [plain, trade_route] |
| old_mine_resource_loop.yaml | old_mine | [mine, underground] |
| ruins_mystery_quest.yaml | haunted_battlefield | [ruins] |
| undead_battlefield.yaml | haunted_battlefield | [ruins] |
| goblin_camp_conflict.yaml | goblin_camp | [forest] |
| scalable_bandit_camp.yaml | bandit_road | [forest] |
| bandit_road_trade_pressure.yaml | bandit_road | [wilderness] |
| moon_cult_ruins.yaml | moon_cave | [cave] |
| mountain_pass.yaml | mountain_pass_zone | [mountain] |
| nomadic_herd.yaml | near_forest | [plain] |
| forest_warden_grove.yaml | sacred_grove | [forest] |
| forest_warden_grove.yaml | deep_forest | [forest] |
| wolf_den_near_forest.yaml | near_forest | [forest] |
| wolf_den_near_forest.yaml | wolf_den | [forest] |

No changes needed for `forest_deep_ecology` (no regions; `wilderness` satisfied by type-matched regions in assembled world).

## Step 6: Re-compile All Worlds

Use the CLI or direct API to recompile dungeon_crawl, urban_political, wilderness_survival, generated_frontier_3_42, and verify zero quest location warnings.

## Step 7: Add New Unit Tests

In `tests/unit/worldbuilding/test_world_compiler.py`, add three tests:
- `test_quest_location_tag_matches_region_type`
- `test_quest_location_tag_matches_region_explicit_tag`
- `test_quest_location_tag_warns_on_genuine_mismatch`

## Step 8: Run Scoped Tests

```bash
pytest tests/unit/worldbuilding/ -v --timeout=60
pytest tests/integration/worldassembly/ -v --timeout=120
```
