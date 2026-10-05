---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER
phase: done
date: 2026-10-05
tags: [world]
---

# investigation — TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER

The Scope 1 audit, the first-match finding, the shadowing measurements and the 3-arm A/B are in the ticket's Implementation Notes; the raw runs are in `probes/` (see `probes/README.md`).

## Measured result of the unified rule (frontier_living_world, 10,000 ticks, seed 42)
The rule unifies the lookups and repairs the far-edge/inclusive-edge disagreement (`hometown` 12 deaths credited, was 7; credited to no region 16, was 23). It does **not** un-shadow `near_forest`, `wolf_den` or `trading_hometown`: they remain 0.0 trauma. The regions overlap partially, none nested: near_forest∩wolf_den 500, near_forest∩bandit_road 675, wolf_den∩bandit_road 600 tiles, so the 60x20 `bandit_road` strip (area 1,200) is smaller than `wolf_den` (1,400) and `near_forest` (2,025) and wins every shared point. Area is not a proxy for specificity under partial overlap.

## Second, opposite precedence (evidence for authored precedence)
`data/content/world_modules/wolf_den_near_forest.yaml:24-31` documents that `near_forest`/`wolf_den` process last (alphabetical tie-break in `topological_sort_modules()`), so tiles inside their bounds that belong to `bandit_road` get forest/swamp noise-fill instead of the road's terrain. Terrain fill says forest wins those tiles; smallest-area region lookup says road wins them. Two precedence rules disagree about the same tiles, which is the strongest argument that precedence must be authored, not derived from geometry.

## Other results
- Trauma crosses 50 in two regions: `goblin_camp` tick 5211, `bandit_road` tick 5317 (was 5217); ~111/~110 by tick 10,000. ENV-06 stays reachable.
- `generated_frontier_3_42` (measured after the change only, no before-run; regions hometown, bandit_road, goblin_camp, moon_cave, old_mine, orc_stronghold): 138 deaths in 10,000 ticks; 131 lie in exactly one region, 3 in two (`bandit_road` + `goblin_camp`), 4 in none. Credited: goblin_camp 105, hometown 12, bandit_road 8, old_mine 5, moon_cave 4, none 4. `goblin_camp` crosses 50 at tick 6911. Overlap is nearly absent in that world, so the shadowing finding is specific to `frontier_living_world`. Output: `probes/after_smallest_area_gf342_10000_*`.
- Worlds not re-measured: the other 22 corpus worlds. The audit of which of them overlap is `TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE`'s corpus probe.
