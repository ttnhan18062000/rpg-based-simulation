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

**Qualification (2026-10-05): every `frontier_living_world` figure in this ticket is an INDICATION, not a reproducible value.** Those runs were taken without `audit_mode` and without the tick budget disabled, and `Kernel` drops work when wall-clock compute time exceeds the budget (`kernel.py:466-469`), so non-audit runs depend on machine load (`TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT`). Affected: the trauma crossing ticks (5211, 5317, 5217), `hometown` 7 to 12 credited deaths, the 275 and 141 death counts, and the 5,000-tick and 10,000-tick series. The static geometry (partial overlaps, areas, `bandit_road` being smaller than `wolf_den` and `near_forest`) never ran a simulation and stands. The `generated_frontier_3_42` runs are deterministic (identical across repeated runs) and stand as values.

## LOC-08 rework: the fiction refutation test, measured (audit_mode, budget off, seed 42, 10,000 ticks)
`LOC-08` names three ways the rule is refuted; two are checked by tests (consistency: `tests/unit/worldbuilding/test_region_precedence_compile.py`; shadowing: `test_every_resolved_world_has_every_region_owning_a_tile`, plus the 3c error at assembly). The third is fiction: contested-zone deaths dominated by the declared loser's population. Before the rule, undead (`undead_remnants`, immune only to `UNDEAD_CORRUPTION`) died of a neighbour's hazard on battlefield ground. After, with the ratified `haunted_battlefield` wins in force (outputs `probes/loc08_zones_*.jsonl`, probe `probes/zones_loc08.py`):
| world | undead deaths before / after | of those, in a contested zone before / after |
|---|---|---|
| frontier_living_world | 4 / 1 | 4 / 0 |
| frontier_extended | 1 / 1 | 1 / 0 |
| simq_scale_stress_seed42 | 6 / 1 | 6 / 0 |
| lifecycle_full_coverage_world | 6 / 0 | 6 / 0 |
| hero_guild_routing | 6 / 0 | 6 / 0 |
All 23 contested-zone undead deaths are gone: the undead now take `haunted_battlefield`'s hazard (which they are immune to) on its overlaps with `goblin_camp`, `mountain_pass_zone` and `river_ford`. The remaining 1 undead death in three worlds is outside any contested zone. Caveats: "before" is the earlier base `54c31ee73`, "after" is this branch on `origin/main` `58aa22f67`, so total death counts differ for unrelated reasons (the bosses and the combat fixes); the boss loop is untouched here (decision 14/15 live on another branch). The `bandit_road` boss, spawning at (70,50) inside `bandit_road`, `near_forest` and `wolf_den`, is still credited to `bandit_road` (72 to 79 deaths), as ratified (`bandit_road` beats both).
The fourth refutation (stability across a runtime region `kind` rewrite) holds by construction: the order is fixed in the resolved world and nothing in it reads `kind`.
