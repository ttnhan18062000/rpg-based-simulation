---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: investigation
tags: [engine, combat]
---

# Investigation: does an ATTACK task that fails OUT_OF_RANGE repeat?

## Method
`probes/oor_probe.py` wraps `CombatActions.execute_attack`, records the legality verdict each call saw, and counts
`OUT_OF_RANGE` verdicts, repeats (the same attacker's previous `execute_attack` verdict was also `OUT_OF_RANGE` against the
same target) and the length of each streak. Tree: `origin/main` `7a9f302db` (contains #344 and #347) plus ticket files only,
so source is identical to main. Settings: `audit_mode=True`, `max_tick_budget_ms=1e9`, seed 42, 2000 ticks, one simulation
at a time, every world run twice. Both runs matched exactly in all four worlds, so these are **values**, not samples.

## Result (value)
| world | execute_attack calls | LEGAL | TARGET_INCAPACITATED | OUT_OF_RANGE | repeats | longest streak |
|---|---|---|---|---|---|---|
| crowded_frontier | 0 | - | - | 0 | 0 | - |
| urban_political | 0 | - | - | 0 | 0 | - |
| dungeon_crawl | 4 | 2 | 2 | 0 | 0 | - |
| frontier_living_world | 7 | 3 | 2 | 2 | 1 | 2 verdicts, 1 tick |

The one repeat is two `OUT_OF_RANGE` verdicts for one pair inside a single tick, not a task surviving across ticks.
Lane A's "three of the first four calls rejected OUT_OF_RANGE" was a single pre-#344 / pre-#347 sample and is **not
reproduced** on current main: it must not be carried forward.

## What the measurement does and does not show
- It shows the repeat is bounded on current main: no streak crosses a tick boundary in any world.
- It does **not** show the repeat cannot happen. Only 11 `execute_attack` calls occur in 4 x 2000 ticks, because the
  decision-driven attack path is still mostly closed upstream (the flee gate, ticket
  `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-...`, blocked on ratification). A task that is held after `OUT_OF_RANGE`
  is reachable by construction (`actions.py:221-230` resets only `TARGET_INCAPACITATED`). It is unobserved, not
  unreachable.

## Decision
Scope 2 permits scaling the change down to nothing when the repeat is bounded. Recorded rule: **no change to the action
pipeline**. Reasons: the measured repeat is one tick; a reset on `OUT_OF_RANGE` would be unobservable in any corpus world
today (nothing to re-measure, nothing for a disabling control to bite on beyond a synthetic fixture); and changing the
sticky-task reset in a phase the planner holds only for this family, on a defect with no measured instance, is the global
weakening the ticket's Out of Scope warns against.

Open question (multiplied vs base range): moot with no change. Recorded for whoever reopens it: `legality.py:284` judges
reach against `attacker.combat.range * perception multiplier`, so a reset keyed to "left reach" must use that same value,
or bad weather re-introduces the sticky task.

## Re-open trigger
Re-run `probes/measure.sh` after the flee-gate ticket lands and the attack path opens. If any streak crosses a tick
boundary, implement the reset (candidate: `OUT_OF_RANGE` joins `TARGET_INCAPACITATED` in `is_unrecoverable_attack_failure`
only when the target is a live entity beyond `legality.py`'s effective range) with a disabling-control test.
