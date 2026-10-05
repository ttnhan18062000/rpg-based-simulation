---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK
artifact_type: investigation
tags: [combat, strategy, cognition]
---

# Investigation: why entities adjacent to a live target never attack

All numbers are **single runs** (`seed 42`, 2000 ticks, `audit_mode=True`, `max_tick_budget_ms=1e9`,
`LocalSequentialExecutor`) on a branch **without** the `DirtySetBuilder` determinism fix
(`TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK`), so each is a sample. The probe scripts are in
`probes/` (see its README for how to re-run). Line numbers are at the commit of this branch, derived after the entity-target
fix, not carried from the ticket.

## The answer to the ticket's main question: never attempted, not rejected

`crowded_frontier`: 1953 samples of a live entity holding an ACTIVE `defeat_enemy` objective within Manhattan 1 of its live target.
In **1953 of 1953** the attacker's readiness was at least 100 and `TacticalDecisionSystem.evaluate_entity_intent` was **not
called** that tick; no attack-legality verdict was issued. Traced entity 19 against 15: the tactical pass runs once at tick 1
(distance 3) and emits an `ENTITY_MOVE` in mode `PURSUE` with `target_id` 15; distance 1 at tick 3; from then on the task stays
`ENTITY_MOVE`, the pass is never called again, and the two entities swap between the same two tiles every tick.

## The chain is three gates deep

1. **Sticky pursuit task (fixed here).** `DeterministicScheduler.select_work` (`src/engine/scheduler.py`) keeps an entity whose
   task is already `ENTITY_MOVE` or `ENTITY_ACT` as that work kind without re-invoking the decision (`docs/engine/kernel.md`,
   the Sticky-Task Law). The `ENTITY_MOVE` dispatchers (`executor.py`, `worker_logic.py`) only re-asserted the navigation target;
   nothing ended the task. The only resets back to the brain that exist are survival-action success and an `ATTACK` failing
   `TARGET_INCAPACITATED` (`pipeline_phases/actions.py`). Same defect as the objective that never terminated
   (`TCK-20261002-...`), one layer down: a task with no termination condition.
2. **Brain cadence (not changed).** Once the task is idle (`ENTITY_ACT`, empty payload), `scheduler.py` treats it as a brain tick
   gated by `should_run(tick, id, strategic_intelligence cadence = 10)`, so the entity waits about 5 ticks on average. Not
   confirmed to matter on its own because of gate 3. `scheduler.py` is ruled contested and was not touched.
3. **The flee gate (its own ticket).** `if emotion.is_fleeing` is checked before the hostile scan and before any attack. A forced,
   read-only `evaluate_entity_intent` call on 147 real `crowded_frontier` states with a live catalog-hostile adjacent decided
   `ATTACK` once, a plain move 3 times and **`PANIC_RETREAT` 143 times (97%)**, 116 of them at hp 0.4 or better (examples hp 0.81
   and 0.99). Recomputing the documented panic terms: **regional trauma contributed to 145 of 145 flees; the outnumbered ratio to 0;
   nemesis/grudge to 0.** Regional trauma rises **+1.0 per death, uncapped** (Bible 05 section 2; `world_dynamics.py`), and the
   appraisal adds `0.5 * trauma` to a panic score whose flee threshold is 0.4: one death in a region flips most entities, two flip
   all, at any HP or bravery. Trace: all regions 0.0 at compile; `goblin_camp` 1.0 after one death at tick 3, `bandit_road` 2.0 after
   two at tick 6. A units mismatch between a death counter and a 0..1 dread scale, filed as its own ticket by the planner; the
   mapping is a semantics decision and was not changed here.

## A fourth finding inside gate 1: the objective and the task fought

After the pursuit ended and the navigation target was cleared, entity 19's target **reappeared at tick 5** at the creation-time
snapshot. Writer: the strategic redirection block (`intelligence.py`, `redirection.py`) sets `NavigationUpdate(target_set =
active_obj.target_position)` for the ACTIVE objective whenever no other navigation update is pending, and `target_position` is the
snapshot. The stale-point defect of `TCK-20261002` survived in a second writer (that ticket fixed the reader). Confirmed by A/B on
the same trace: with the writer changed, the navigation target stays `None` from tick 4 to tick 10.

## Results (single runs; before = the #342 head, after = this branch)

| | before | after |
|---|---|---|
| tile-swap tick-pairs, `crowded_frontier` | 975 | **2** |
| tile-swap tick-pairs, `frontier_living_world` | 1809 | **2** |
| tile-swap tick-pairs, `urban_political` | 978 | **3** |
| tile-swap tick-pairs, `dungeon_crawl` | 1 | 1 |
| `crowded_frontier` decision-path `execute_attack` | 0 | 0 |
| `frontier_living_world` `execute_attack` / `resolve_attack` | 5 / 1 | 4 / 4 (9 / 7 in a run with the dispatch change alone) |
| adjacent-to-live-target samples, `crowded_frontier` | 1953 | 75 |

The tile-swap collapse (two orders of magnitude, three worlds, unchanged where there was nothing to fix) is the robust effect.
Decision-path attack counts are noisy (the two post-change runs on `frontier_living_world` differ by more than the change
explains) and `crowded_frontier` stays at 0: gates 2 and 3 remain. **No claim of an engagement improvement is made.**

## Scope 2: one defect or two

Two. `frontier_living_world` before: 5 `execute_attack` calls and 1 `resolve_attack`. In the first four recorded calls, call 1 was
legal and resolved; calls 2 to 4 were rejected `OUT_OF_RANGE` at readiness 100, all attacker 46 against target 17 (ticks 15, 15,
21): a sticky `ATTACK` task still dispatched after its target moved away (`OUT_OF_RANGE` is deliberately not reset as
"recoverable", `pipeline_phases/actions.py`). That is attempted-then-rejected, the same sticky-task family one task kind over,
and a separate defect (the fifth call was not recorded). After the dispatch change the same world also showed 751
`FRIENDLY_FIRE_ILLEGAL` verdicts that were absent before (before: 15 `OUT_OF_RANGE`, 41 `LEGAL`); the tactical hostile list and
legality's `is_hostile_compat` appear to disagree about who is hostile. Single run, unexamined. Both for their own tickets.

## Scope 4: the incidental opportunity attack as the control

Incidental attacks resolve through `resolve_multi_attack(..., is_opportunity_attack=True)` (`movement.py`, triggered by movement
while engaged), never through the decision pass, so the sticky task cannot starve them. Measured in the same runs: `urban_political`
71 calls before, 72 after (decision-path `execute_attack` 0 / 0); `dungeon_crawl` 24 / 24 (decision-path 4 / 4). The earlier
`resolve_attack`-only counter showed zero opportunity attacks because it hooked the wrong function; corrected.

## Not done

Re-taking these numbers on a tree with the dirty-set fix (the planner asked for it once #344 is on `main`); a world other than the
five measured; the brain-cadence gate in isolation; the sticky `ATTACK` re-dispatch; the friendly-fire verdicts; the flee gate fix.
