---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70
artifact_type: plan
tags: []
---

# plan — TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70

1. Remove the CAMP_SPAWN_INTERVAL spawn block and the raid trigger from `CampService.process_camps`; delete `RaidService.spawn_raid`.
2. Keep the flag-gated nest-spread branch and the natural-creature reproduction step as they are (OFF, retire with M1).
3. Convert the tests of the removed behaviour; add `test_camps_spawn_nothing.py`.
4. Measure paired against rpg-next 56cefc2f4 (frontier_living_world, urban_political, seeds 42-46, 5000 ticks), then the gate harness V8 on the camp worlds.
5. Docs: divergence 2.125, WORLD-030/031/032 divergent, Bible 05 subsection, mechanism comment. Remove the V8 known-red entry only if V8 is green.
