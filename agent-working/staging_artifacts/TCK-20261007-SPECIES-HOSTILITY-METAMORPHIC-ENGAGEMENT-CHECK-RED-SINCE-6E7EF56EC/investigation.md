---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC
phase: open
date: 2026-10-07
tags: [combat, regression]
---

# Investigation — TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC (testing rescope)

## Findings
- **Underpowered.** Lane B's bisect (ticket Implementation Notes) classed the red (a): the relation holds, and #395 shrank the effect, so a 3-seed sum fails by chance about 1 run in 4.
- **Not deterministic unpinned.** Seeds 301-340 x 200t at ae3352361 gave 115 vs 140 (Lane B) and 122 vs 141 (testing): the lab path's default governor follows host load (TCK-20260822).
- **Pinned, the stock layout is still too weak.** Deterministic (two runs identical), but +0.475 per seed, SD 2.37, z 1.26 at N=40; about 136 seeds would be needed for z 2.33. 20 x 500t: z 0.80. In most seeds wolves and humans never meet within the horizon: the den (70,30,105,70) is about 30 tiles from `hometown` (10,10,40,40), against a perception radius of 10 (Manhattan, `ENTITY_TARGET_PERCEPTION_RADIUS`, src/systems/strategic_systems/entity_target_objective.py:25).
- **Contact-rich layout (ruling (a)).** Placement is decided only by `PopulationSpec.spawn_region` (uniform draw inside the region's bounds; src/worldbuilding/schema.py:89,210, compiler.py:609-622). Moving `wolf_den` to (41,30,48,40) with its nest at (44,35) keeps factions, declarations, populations and the species mutation unchanged; no leash applies (compiler sets none; default 0). Pinned, seeds 301-340: 73 vs 653, +14.5, SD 8.54, z 10.7, no negative seed, deterministic.
- **No perception/sighting event exists** in the event stream (checked in the source and in a real baseline run's event types), so the non-vacuity guard uses baseline engagement counts.

## Docs Requiring Update
None. Test-only change; the relation and its authority are unchanged (rpg-planner ruling, recorded in the ticket).
