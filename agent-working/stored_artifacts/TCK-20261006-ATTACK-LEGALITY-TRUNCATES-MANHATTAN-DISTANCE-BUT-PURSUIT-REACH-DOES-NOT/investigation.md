---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT
artifact_type: investigation
tags: [combat, cognition]
---

# Investigation

**Question (the ticket's open one):** where do fractional positions come from, intended sub-tile model or a leak?

**Answer: a leak, from one path.** `NavigationSystem.get_next_step` (`src/systems/world_systems/navigation.py`), when the distance is over 50 and the target is `state.town_center`, adds `FlowFieldService.get_flow_direction`'s unit vector (`dx/dist, dy/dist`) to the position. The local step is always +-1 on one axis, so after one flow step every later step carries the fractional offset forever.

Method (read-only probes in `probes/`): `frac_probe.py` wraps `EntityUpdate.__init__` (call site of every fractional `new_position`), `execute_survival`, `_target_in_attack_reach` and the tactical ATTACK decision; `frac_birth.py` classifies every integral-to-fractional transition per entity per tick by whether the flow field produced a step from the entity's old position that tick. Main `6e7ef56ec`, seed 42, 2000 ticks, `audit_mode`, budget off, `LocalSequentialExecutor`, one run per arm (deterministic).

| | crowded_frontier | frontier_living_world |
|---|---|---|
| births of a fractional position | 9 | 13 |
| from a flow-field step | 9 | 13 |
| from any other path | 0 | 0 |
| entities between tiles at the end | 9 of 41 | 13 of 55 |
| ATTACK decisions / float distance above 1 | 17 / 1 | 28 / 4 |
| reach checks / disagreeing with legality | 233 / 7 | 972 / 52 |

Every disagreement is the same direction: pursuit reach says not in reach while legality (truncating) says in reach. The "float distance above 1" ATTACK decisions include ranged attackers, whose reach is above 1 on whole tiles too, which is why one remains after the fix on `crowded_frontier`.

No doc declares sub-tile movement; `docs/combat/combat_movement_overhaul_spec.md:17-18` rules out diagonal movement; occupancy, terrain, buildings and legality all read `int(pos)`. Ruling: Decision 25 (owner delegation, 2026-10-07), an amendment to MOV-07: positions are whole tiles.
