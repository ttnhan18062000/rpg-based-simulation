---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70
artifact_type: test_plan
tags: []
---

# test_plan — TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70

- New `tests/unit/world/test_camps_spawn_nothing.py` (5 tests); 3 of 5 fail on the old code.
- Converted: test_camp_lifecycle, test_calamity_raid, test_global_raid_retired, test_guild_need_scorer (builds the goblin_raider through `spawn_monster`), test_camp_raid_targeting (now a matured-camp-raids-nothing run).
- Paired run base vs change; V8 via the gate harness on frontier_living_world and crowded_frontier.
