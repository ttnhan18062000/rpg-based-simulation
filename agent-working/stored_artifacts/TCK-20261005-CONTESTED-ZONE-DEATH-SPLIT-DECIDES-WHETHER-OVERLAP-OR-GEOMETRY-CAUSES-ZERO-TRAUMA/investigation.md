---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA
phase: done
date: 2026-10-05
tags: [world]
---

# investigation — TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA

All runs: `audit_mode` on, `max_tick_budget_ms=1e9`, seed 42, `PROD_SMALL`, 10,000 ticks. `frontier_living_world` reproduced **byte-identically** across two runs, so these are values. **Primary base: `54c31ee73`** (main `7a9f302db` incl. #347, plus the region-lookup unification, no hazard-growth change). A second set was taken earlier on the hazard-growth tip `198145e00` (descends from #346, before #347, hazard cap removed); it is cited where it adds a world. Both bases give the same verdict.

## What the deaths are (this changes the question)
`frontier_living_world`, primary base: **233 deaths, 232 are `HAZARD` (environmental drain, no killer), 1 is a `DEFEAT`.** **158 (68%) are `world_boss` deaths**: a boss appears from tick 2111 about every 100 ticks, one in `goblin_camp` and one in `bandit_road` (79 each), and dies of hazard drain within a few ticks, at a handful of fixed tiles ((110,37), (110,38), (61,48), (62,57) ...). Another 68 are `goblin_warrior`/`orc_warrior` hazard deaths at two spawn tiles ((110,38) and (87,50)). All victims but seven are `monster_horde`, which has **no hazard immunities**. Credited: `goblin_camp` 117, `bandit_road` 116, **every other region 0**: exactly the two regions that cross trauma 50. Trauma on this world is a respawn-and-die loop at spawn tiles, not fighting. (World bosses are deferred by the owner; the loop runs anyway.) Hazard drain uses the same lookup (`WorldDynamicsSystem._get_region_for_pos`), so the region a tile resolves to also decides which hazard drains the entity there.

## Zone split, `frontier_living_world`, primary base (233 deaths)
| zone | deaths | credited to |
|---|---|---|
| `goblin_camp` only | 97 | goblin_camp |
| `bandit_road` only | 16 | bandit_road |
| road ∩ near_forest ∩ wolf_den (triple) | 34 | bandit_road |
| road ∩ near_forest ∩ **trading_hometown** | 33 (32 world_boss, 1 guard) | bandit_road |
| road ∩ near_forest | 31 | bandit_road |
| goblin_camp ∩ wolf_den | 16 | goblin_camp |
| goblin_camp ∩ haunted_battlefield | 4 (undead sentinels) | goblin_camp |
| 4-way (road, forest, trading, den) | 1 (guard) | bandit_road |
| road ∩ wolf_den | 1 (the one `DEFEAT`: bandit scout kills a wild-beast) | bandit_road |
| **uncontested `near_forest`; uncontested `wolf_den`; `near_forest` ∩ `wolf_den` without road; uncontested `trading_hometown` interior; `trading_hometown` ∩ `near_forest` without road; uncontested `haunted_battlefield`; credited to no region** | **0 each** | |
Physically inside each region's bounds: `goblin_camp` 117, `bandit_road` 116, `near_forest` 99, `wolf_den` 52, `trading_hometown` 34, `haunted_battlefield` 4. Hazard-tip run, same world: triple 74, road∩forest 18, road∩forest∩trading 15; the contested-zone split moves with the base (where bosses die moves), the zero rows do not.

## Owned-tile share under the rule in force (`geometry.jsonl`, `frontier_living_world`)
`near_forest` 200 of 2,116; `wolf_den` 525 of 1,476; `trading_hometown` 1,080 of 1,296; `bandit_road` 1,184 of 1,281; `haunted_battlefield` 1,465 of 1,681; `old_mine` 1,865 of 1,886; `goblin_camp` and `hometown` own all of theirs. (Inclusive tiles; these areas include the +1 per axis and match the planner's table.)

## Verdict
- **H3 holds for own ground.** No death at all occurs on uncontested `near_forest`, uncontested `wolf_den`, or `trading_hometown`'s uncontested interior, in any of the five worlds measured. Nothing in this world fights there; the one `DEFEAT` in 10,000 ticks is on the road.
- **H1 holds for the contested deaths, narrowly.** All 99 deaths inside `near_forest`, all 52 inside `wolf_den` and all 34 inside `trading_hometown` lie in zones shared with `bandit_road`, and all are credited to it. A rule crediting another region would move them. But they are a few spawn tiles' worth of hazard deaths of `monster_horde` entities, not den bloodshed.
- **H2 is not supported.** The road's deaths are not wolf-ecology kills: killers are the environment in 232 of 233 deaths; the only creature kill is bandit-on-beast.
- **H4 cannot be separated from H3.** `near_forest` owns 200 tiles, but nothing happens on its other 1,916 tiles either, so more owned tiles would not by themselves produce trauma. `trading_hometown`'s 34 contained deaths are all in road∩forest∩trading and are credited to the road; a nesting rule would move them to `trading_hometown` (or `near_forest`), which is a credit change, not a trauma-from-fighting change.
- **So the overlap work must not be cited as a trauma fix for fighting**: trauma here comes from world-boss and warrior hazard deaths at spawn tiles. What a precedence rule would change is **which region is credited and which hazard drains** for those spawn tiles.

## The four author-call pairs (the contested zone, with killer/victim)
Refutation test: a declared winner's contested deaths should involve the winner's own population or fiction.
| pair (tiles) | worlds measured | contested deaths | victims / killers | reading |
|---|---|---|---|---|
| `goblin_camp` ∩ `haunted_battlefield` (216) | frontier_living_world 4, frontier_extended 2, simq_scale_stress 1 | 7 | all `undead_remnants` sentinels (the battlefield's own population), killer = hazard drain | credited to `goblin_camp` (smaller). The undead take 30 HP/tick from `goblin_camp`'s `NATURAL_TERRAIN` hazard (3.0); `undead_remnants` is immune only to `UNDEAD_CORRUPTION`, `haunted_battlefield`'s hazard kind, so on that region's hazard they would take none. Evidence for `haunted_battlefield` winning. |
| `mountain_pass_zone` ∩ `haunted_battlefield` (861) | hero_guild_routing 6, lifecycle_full_coverage 6 | 12 | all `undead_remnants`, hazard drain | credited to `mountain_pass_zone` (`PHYSICAL`, 2.5, the smaller): undead die from the pass's hazard that their own region's hazard kind would spare. Same direction: `haunted_battlefield` wins. |
| `haunted_battlefield` ∩ `river_ford` (961) | simq_scale_stress 5 | 5 | all `undead_remnants`, hazard drain | credited to `river_ford` (`PHYSICAL`, 1.0). Same direction. |
| `old_mine` ∩ `sacred_grove` / `deep_forest` (756 each) | frontier_extended, simq_scale_stress | **0** | none | no deaths in the zone in either world: **no evidence either way**; this measurement cannot flip that call. |
Caveat: the three haunted_battlefield pairs rest on 24 deaths across five worlds (1 to 6 per world), but all 24 are `undead_remnants` dying to a hazard they are not immune to while standing on ground that region would have spared them. Consistent, small. Declarations that make `haunted_battlefield` win would change behaviour (these undead would stop dying), not only bookkeeping.

## Second world
Five other overlapping worlds measured (above). `lifecycle_full_coverage_world` adds a different pattern: `near_forest` ∩ `wolf_den` without the road holds 106 hazard deaths credited to `wolf_den` (smallest), again with 0 on uncontested `near_forest`. `generated_frontier_3_42` (earlier, deterministic) has almost no overlap.

## Not done / limits
`quest_dense_frontier` failed at kernel construction (artifact-manifest JSON decode error, not investigated). The other 11 pairs were not measured. One seed. The primary base predates nothing relevant to region resolution, but figures taken on a different base will differ in the contested-zone split (shown above).
