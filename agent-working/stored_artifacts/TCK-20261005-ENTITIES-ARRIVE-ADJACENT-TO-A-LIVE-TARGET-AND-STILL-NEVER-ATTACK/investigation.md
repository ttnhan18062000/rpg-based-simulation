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

All numbers below were **re-taken on the rebased tree** (`origin/main` `544b1d341`, which contains the `DirtySetBuilder`
determinism fix `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK`, plus this ticket's two commits).
Setup: `seed 42`, 2000 ticks, `audit_mode=True`, `max_tick_budget_ms=1e9`, `LocalSequentialExecutor`, one simulation at a time.
"Before" is a clean `origin/main` worktree (no pursuit fix); "after" is this branch. Labels: **value** = the identical
run was repeated and gave identical counters (the fix tree, two runs per world, all four worlds); **sample** = one run (the
control tree, and every read-only probe). No pre-`#344` number from the first pass of this investigation is carried forward.
The probe scripts are in `probes/` (see its README for how to re-run). Line numbers are at the commit of this branch.

## The answer to the ticket's main question: never attempted, not rejected

`crowded_frontier`, clean `origin/main` (one run, a sample; `probes/adj_probe.py`): 1953 samples of a live entity holding an ACTIVE
`defeat_enemy` objective within Manhattan 1 of its live target. In **1953 of 1953** the attacker's readiness was at least 100 and
`TacticalDecisionSystem.evaluate_entity_intent` was **not called** that tick (2 of the 1953 had an attack-legality verdict
issued, both `LEGAL`). This reproduces the first-pass figure on the post-`#344` base. On this branch the same probe gives
**281** samples, and the tactical pass is still **not called in 281 of 281** (1 legality verdict): ending the pursuit makes the
adjacency 7 times rarer, but it does not by itself make the decision pass run during it (gates 2 to 4). Traced entity 19 against 15: the tactical pass runs once at tick 1
(distance 3) and emits an `ENTITY_MOVE` in mode `PURSUE` with `target_id` 15; distance 1 at tick 3; from then on the task stays
`ENTITY_MOVE`, the pass is never called again, and the two entities swap between the same two tiles every tick.

## The chain is four gates deep (gate 4 added after the re-measurement)

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
   read-only `evaluate_entity_intent` call (`probes/forced_brain.py`, one run, a **sample**) on 353 real `crowded_frontier`
   states with a live catalog-hostile adjacent decided: `PANIC_RETREAT` 141 (40%; 114 of them at hp 0.4 or better, 27 below),
   `BRACKETING` 194 (55%), `ATTACK` 15 (4%), a plain move 3. **The first pass of this investigation claimed `PANIC_RETREAT` 143 of
   147 (97%) and "everyone flees"; that does not reproduce and is withdrawn.** The population also changed (147 to 353 calls), so
   the difference is not attributable to the determinism fix alone. What survives: recomputing the documented panic terms
   (`probes/panic_terms.py`, entity-ticks, not unique entities, so rows repeat for the same entities; it recomputes the terms, it
   does not record what the brain did) regional trauma is present in every flee sample (`crowded_frontier` 143 of 143 at
   trauma >= 0.8; `frontier_living_world` 34 of 35), panic saturates at trauma 3.0, and on `frontier_living_world` the
   outnumbered ratio appears alongside trauma (the first pass said 0). It is not a rate over entities. Regional trauma rises **+1.0 per
   death, uncapped** (Bible 05 section 2; `world_dynamics.py`) and the appraisal adds `0.5 * trauma` to a panic score whose flee
   threshold is 0.4; a units question (a death counter on a 0..1 dread scale) filed as its own ticket by the planner. The mapping is
   a semantics decision and was not changed here.
4. **`BRACKETING` repositioning moves (named by the planner after the re-measurement; its own ticket).** The 194 `BRACKETING`
   decisions are `ENTITY_MOVE` with movement mode `REPOSITION` and a live entity `target_id`, the same shape as the pursuit defect.
   `pursuit_reached_attack_range` returns `False` unless the mode is `PURSUE` (a deliberate exclusion so guard and cover moves keep
   their own lifecycle), so a `BRACKETING` move is not ended by this fix. Whether those moves really go sticky, versus entities
   merely choosing `BRACKETING` often, and whether `bracket_pos` is a snapshot, are **unmeasured here**: see
   `TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`. Not touched by this ticket.

## A fourth finding inside gate 1: the objective and the task fought

After the pursuit ended and the navigation target was cleared, entity 19's target **reappeared at tick 5** at the creation-time
snapshot. Writer: the strategic redirection block (`intelligence.py`, `redirection.py`) sets `NavigationUpdate(target_set =
active_obj.target_position)` for the ACTIVE objective whenever no other navigation update is pending, and `target_position` is the
snapshot. The stale-point defect of `TCK-20261002` survived in a second writer (that ticket fixed the reader). Confirmed by A/B on
the same trace: with the writer changed, the navigation target stays `None` from tick 4 to tick 10.

## Results (before = clean `origin/main` `544b1d341`, one run, a sample; after = this branch, two identical runs, a value)

| | before | after |
|---|---|---|
| tile-swap tick-pairs, `crowded_frontier` | 975 | **2** |
| tile-swap tick-pairs, `frontier_living_world` | 1809 | **1** |
| tile-swap tick-pairs, `urban_political` | 978 | **3** |
| tile-swap tick-pairs, `dungeon_crawl` | 1 | 1 |
| decision-path `execute_attack` calls, `crowded_frontier` | 0 | 0 |
| decision-path `execute_attack` calls, `frontier_living_world` | 5 | 7 |
| `resolve_attack` non-opportunity, `frontier_living_world` | 1 | 3 |
| decision-path `execute_attack` / non-opportunity `resolve_attack`, `dungeon_crawl` | 4 / 2 | 4 / 2 |
| opportunity attacks, `urban_political` | 71 | 72 |
| opportunity attacks, `dungeon_crawl` | 24 | 24 |
| opportunity attacks, `crowded_frontier` | 488 | 283 |
| opportunity attacks, `frontier_living_world` | 38 | **644** |

The tile-swap collapse (two orders of magnitude on three worlds, unchanged on the world where there was nothing to fix) is the
robust effect, and it matches the first-pass figures within a tick or two. Decision-path attacks rise only slightly
(`frontier_living_world` 5 to 7) and `crowded_frontier` stays at 0: gates 2, 3 and 4 remain. **No claim of an engagement
improvement is made.** Adjacent-to-live-target samples on `crowded_frontier` (`adj_probe.py`, one run each): 1953 before, 281 after
(tactical pass not called in either case: 1953 of 1953, 281 of 281). The first pass reported 75 after; that was pre-`#344` and is
replaced.

**Unexplained: the opportunity-attack controls moved.** I called this counter "unchanged" in the first pass (71/72, 24/24); on this
base two worlds hold (`urban_political`, `dungeon_crawl`) but `frontier_living_world` goes 38 to 644 and `crowded_frontier`
488 to 283, in opposite directions. One mechanism should not produce opposite signs, so something is unaccounted for. A
hypothesis, **unmeasured**: ending pursuit moves leaves entities adjacent longer, which gives movement-while-engaged more chances to
trigger. Not tested, not a claim, and the PR does not rest on it.

## Scope 2: one defect or two

Two. A first-pass observation, **not re-taken on this base** (pre-`#344` single run, kept only as the lead the planner filed from, not
as a value): on `frontier_living_world` a sticky `ATTACK` task was still dispatched after its target moved away and was rejected
`OUT_OF_RANGE` (`OUT_OF_RANGE` is deliberately not reset as "recoverable", `pipeline_phases/actions.py`): the same sticky-task
family one task kind over, a separate defect (`TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES`). The
first pass also saw 751 `FRIENDLY_FIRE_ILLEGAL` verdicts after the dispatch change; the tactical hostile list and legality's
`is_hostile_compat` appear to disagree about who is hostile (`TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE`).
That count is also pre-`#344` and is not carried as a value; both tickets measure first.

## Scope 4: the incidental opportunity attack as the control

Incidental attacks resolve through `resolve_multi_attack(..., is_opportunity_attack=True)` (`movement.py`, triggered by movement
while engaged), never through the decision pass, so the sticky task cannot starve them. They are the control for "does the
decision path ever attack": see the table above for the re-taken counts and the unexplained `frontier_living_world` and
`crowded_frontier` shifts.

## Pre-existing on main, not caused by this change

`probes/brain_adj.py` on `frontier_living_world` prints 10 `LAW-OCCUPANCY-COLLISION` hard-law errors (entity 18 against 53, 55, 57
on tile (87, 50)) on **both** the clean `origin/main` control tree and this branch (10 and 10). Filed by the planner as
`TCK-20261005-LAW-OCCUPANCY-COLLISION-HARD-LAW-ERRORS-ON-MAIN`.

## Not done

A world other than the five measured; the brain-cadence gate in isolation; the sticky `ATTACK` re-dispatch; the friendly-fire
verdicts; the flee-gate fix; the `BRACKETING` gate; a per-entity de-duplicated panic breakdown; the mechanism behind the
opportunity-attack shifts.
