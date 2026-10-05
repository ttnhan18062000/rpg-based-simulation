---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: investigation
tags: [engine, combat]
---

# Investigation: does an ATTACK task that fails OUT_OF_RANGE stay held?

## Method
`probes/oor_probe.py` wraps `CombatActions.execute_attack` and counts the `OUT_OF_RANGE` verdicts it saw, repeats of the
same verdict for the same pair, and streak length. `probes/oor_follow.py` then follows the attacker's **task** (work kind,
payload action/target/outcome, distance, target liveness) for the whole run after each `OUT_OF_RANGE` verdict.
Tree: `origin/main` `7a9f302db` (contains #344 and #347) plus ticket files only, so source is identical to main.
Settings: `audit_mode=True`, `max_tick_budget_ms=1e9`, seed 42, 2000 ticks, one simulation at a time.

## Result 1: verdict counts (value: every world run twice, pairs matched)
| world | execute_attack calls | LEGAL | TARGET_INCAPACITATED | OUT_OF_RANGE | repeat verdicts |
|---|---|---|---|---|---|
| crowded_frontier | 0 | - | - | 0 | 0 |
| urban_political | 0 | - | - | 0 | 0 |
| dungeon_crawl | 4 | 2 | 2 | 0 | 0 |
| frontier_living_world | 7 | 3 | 2 | 2 | 1 (same tick) |

**This table alone is misleading and an earlier version of this file drew the wrong conclusion from it** ("bounded, no
change"). It counts verdicts, and a held task that never re-dispatches produces no further verdicts. It cannot see a held task.

## Result 2: the task, followed (sample: `oor_follow.py` is deterministic and its t157 event matched the counting run, but it
was run three times only for the windowing, not as a repeated matched pair)
The only `OUT_OF_RANGE` episode: attacker 34 against target 11, tick 157, distance 2, readiness 50 (the verdict's own
-50 penalty). Then:
- t158 to t163: distance 1 (in reach), readiness regenerates 60 -> 100, task still `ENTITY_ACT` / `ATTACK` / target 11.
- from t163: the payload outcome reads `SUCCESS` (left over, `reason` still `OUT_OF_RANGE`); **no further
  `execute_attack` verdict for attacker 34 appears at any later tick** (the full verdict list shows 34 only at t157).
- the target walks away to distance 7 by t172 and holds there; the attacker's task is unchanged.
- the task signature (work kind, action, target id) does not change again until **t1008, when target 11 dies**.
So the attacker held an `ENTITY_ACT ATTACK` task for about 851 ticks without re-deciding and without dispatching an attack.

## What is and is not explained
- Explained: nothing ends the task. The `OUT_OF_RANGE` failure is annotated into the payload and the task is kept
  (`actions.py:227-244`), so it is not an empty payload and `scheduler.py`'s idle test never reclassifies it to a brain tick.
- **Unexplained:** why the held task does not even re-dispatch `execute_attack` once readiness is back at 100 and the target
  is adjacent (t164-t166). Not yet traced; do not attach a mechanism until it is.
- One entity, one event, one world. The defect is real on main; its frequency is not established. The planner's earlier
  inference ("no streak crosses a tick, so something already ends it") was wrong for the same reason this file's first
  version was: verdict streaks do not see a silent task.

## Decision
The scale-down-to-nothing outcome is **withdrawn**. The ticket's scopes 3-5 apply: reset the task on `OUT_OF_RANGE` when the
target is a live entity that has left reach (judged against `legality.py:284`'s multiplied range), correct the
`actions.py:221-230` comment, and add tests with a disabling control. Whether the reset alone fixes the silent hold, or
the missing re-dispatch is a second defect, depends on the unexplained item above.
