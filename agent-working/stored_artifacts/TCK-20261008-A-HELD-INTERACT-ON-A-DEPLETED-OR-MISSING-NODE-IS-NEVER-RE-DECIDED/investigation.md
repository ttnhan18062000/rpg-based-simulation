---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED
artifact_type: investigation
tags: [ecology, economy, resource]
---

# Investigation

## Finding
`scheduler.py` treats an `ENTITY_ACT` with a non-empty payload as an action to re-run (only an empty payload reclassifies the entity as `ENTITY_BRAIN`). `ActionRouter` annotates a finished action with `outcome=SUCCESS` and keeps the payload. `CoreActions.execute_interact` always returned an interaction update and no failure, even for a node with no charges, and `HarvestSystem` only resets the interaction. So an entity on `INTERACT` against an exhausted node was dispatched the same no-op every tick. Probe (crowded_frontier, seed 42, 1000 ticks): entity 4 from tick about 100 to 900, `task = INTERACT target 10002 outcome SUCCESS`, hunger 6 to 90, and `evaluate_entity_intent` called for it 3 times in the whole run.

The held ATTACK already has this fix for `TARGET_INCAPACITATED` and `OUT_OF_RANGE` (`TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`, `TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`); INTERACT had none.

## Measurement (pinned NORMAL governor, audit_mode, budget off, LocalSequentialExecutor, seeds 42-46, 1500 ticks)
Base = PR 1 (#426, 63793b0ec; regrowth on); new = PR 1 plus this change; the new arm run twice, 15 of 15 digests identical. The first attempt of the new arm failed with ENOSPC (the disk was full); the 30 runs were repeated after space was freed and the earlier partial outputs discarded. Probe `probes/regrow_ms.py`, driver `probes/job3.sh` and `probes/jobs3.txt`, per-run rows `probes/held_interact_runs.jsonl`. Mean (SD) over 5 seeds, base to new:

| world | metric | base | new |
|---|---|---|---|
| crowded_frontier | alive t=1000 | 6.2 (3.1) | 6.0 (1.2) |
| | alive t=1100 | 2.8 (1.3) | 4.8 (1.1) |
| | deaths | 37.0 (1.7) | 36.0 (2.0) |
| | starvation deaths | 13.0 (5.0) | 10.0 (5.0) |
| | charges harvested | 17.8 (5.5) | 13.4 (4.8) |
| | charges regrown | 11.8 (3.3) | 10.6 (3.2) |
| frontier_living_world | alive t=1000 | 15.4 (1.7) | 17.2 (3.1) |
| | alive t=1100 | 13.4 (1.8) | 16.2 (2.3) |
| | deaths | 43.0 (2.3) | 40.0 (2.8) |
| | starvation deaths | 17.6 (3.9) | 14.0 (5.5) |
| | charges harvested | 17.4 (6.9) | 13.2 (4.6) |
| | charges regrown | 12.0 (3.5) | 10.8 (3.3) |
| urban_political | alive t=1000 | 12.0 (3.9) | 13.2 (4.3) |
| | alive t=1100 | 5.6 (3.2) | 9.8 (4.4) |
| | deaths | 24.8 (3.2) | 20.6 (4.7) |
| | starvation deaths | 14.0 (3.4) | 7.6 (1.8) |
| | charges harvested | 19.2 (2.9) | 15.8 (1.9) |
| | charges regrown | 13.0 (1.2) | 12.2 (1.5) |

Reading: released gatherers survive better (alive at t=1100 up in all three worlds, starvation down in all three) and gather somewhat fewer charges, because they no longer spend ticks repeating a no-op or finishing a harvest session on an empty node. Differences are mostly within 1 to 2 SD of five seeds; reported, not tuned. Every run differs from base (0 of 5 digests identical per world), as expected for a change that releases every gatherer.
