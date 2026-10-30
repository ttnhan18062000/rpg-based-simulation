---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT
artifact_type: test_plan
tags: []
---

# Test plan

- `tests/unit/engine/test_a_chosen_rest_lasts_until_the_sleep_need_is_met.py`: the floor and re-export; a REST at the wake line is not ended by it; a sleep from 90 ends strictly below 20; a collapse keeps 58.8 and a sleep chosen after it runs to the floor; failures and non-sleep actions as before.
- `tests/unit/engine/test_the_brain_is_woken_as_a_chosen_rest_ends_at_the_floor.py`: real Kernel, entity ids 1-10 (cadence offsets 0-9), REST in place and an inn-bed SLEEP: project COMPLETED on the tick after the end, no payload within 10 ticks, never REST_IN_PLACE; the predicate's negatives.
- `tests/unit/engine/test_threat_wakes_a_sleeper.py`: adjacent hostile, ranged acting attacker, collapse at 98 re-collapses, a woken sleeper answers (no REST), no-threat and passive/far/other-target negatives, an awake holder unaffected, NEED_WAKE_CADENCE >= ADJACENCY_WAKE_COOLDOWN.
- `tests/unit/engine/test_sleep_debt_stages.py` updated: the wake-line end is a collapse's.
- Paired run (base ba7aa11bd vs new): asleep share, stall runs within 2-6 tiles, door-tile occupancy, collapses, deaths by cause, asleep-at-death, sleeps ended by threat, hits with no wake (0), rest_in_place within 10 ticks of a floor-end (0). STOPs go to rpg-planner.
