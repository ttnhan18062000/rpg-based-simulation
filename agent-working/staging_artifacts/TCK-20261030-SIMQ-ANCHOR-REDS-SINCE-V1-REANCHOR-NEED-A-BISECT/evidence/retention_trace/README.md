# Retention trace and width count (rpg-designer ruling 2; rpg-planner relay; slot go: answers 1-2 plus 30 runs for 3-4, 2000t)

Measurement only, read-only logging in scratch (`/data/vboxuser/Work/simq_retention/`; the scripts are in this directory and the logs, 4 MB, stay in scratch). Wrapper as in the sweep: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, PYTHONHASHSEED=0, audit_mode, sequential, MemAvailable >= 3 GB before each run, setsid, resumable (`run6.sh`). 30 runs (3 worlds x seeds 42-46 x a25619971 and d914bace7) started 14:04, last one done 16:06 (urban 170-250 s, crowded 180-280 s, frontier_living_world 300-370 s per run); plus one extra s42 re-run at d914bace7 (194 s, `rerun.sh`). No hang.

## How the worlds and seeds were run
`probe6.py` calls `tools.calibrate_simq._run_engine(world, seed, 2000, extra_flags=<profile flags of the same name>, audit_mode=True)`, in-process: the engine path `tools/evaluate_simq.py` -> `calibrate_simq` uses for an anchored key (10 entities, compiled world loaded by name; profile feature flags via `_load_profile_feature_flags(_resolve_profile(world))`: for urban_political ENABLE_SOCIAL_COOPERATION and ENABLE_BELIEF_ASSIMILATION on, as in the sweep's log; crowded_frontier and frontier_living_world as `_resolve_profile` gives them, the sweep's logs show no flags line for crowded_frontier). It skips the quality-report replay because seeds 43-46 have no anchored key. Each run's own scratch run directory is deleted after the run (the final `state_hash` from `run_manifest.json` is kept in the log).

## Positive controls (both reproduced exactly)
- urban_political s42 at d914bace7: final state hash `a745defa550623d8` (equal to the sweep's and to the designer-check probe's); entity 18 holds proj_combat_retreat_42 on 1350 ticks (t43-52 and t63-1402), 950 of them after t452. The re-run gives the same hash and the same counts.
- urban_political s42 at a25619971: hash `acb94e8b705817a4`, equal to the sweep's; no retreat holder.
For the other 28 keys no earlier hash is known. frontier_living_world s45 gives the same hash at both commits (`8e27c4ae14befb77`): #769 does not change that trajectory.

## Probe versions (what each run logged)
probe6.py changed twice while the chain ran; each change only adds read-only log records. v1 (runs 1-2: urban s42 d914bace7 and a25619971): pj, rh, sel, sw, dead, fin. v2 (from run 3, started 14:11): adds ex, cap, esc, res (the existing project of the best kind; has_project_capacity; escalated_need_wins; resume_project). v3 (from the first run started after about 14:25): adds work_kind and action to rh. The version of each file is not recorded (a run with no retreat holder logs the same records in every version). The width and dead-entity counts use only fields all versions log (pj, the common fields of rh, dead). Equivalence check: the s42 d914bace7 re-run (v3) against the first run (v1): final hash equal (`a745defa550623d8`); pj, dead, sel and sw records identical; rh identical on the common fields. So the extended probe does not change results.

## Definitions (width, answers 3 and 4)
- Held retreat project: an ALIVE entity's current project id contains `combat_retreat`, per tick. A project is (entity, project id).
- Present threat at a held tick: `acting_threat_to` (src/ai/goals/present_threat.py: a perceived hostile's current task attacks or pursues the subject, or it hit the subject within NEED_WAKE_CADENCE ticks) OR a perceived hostile orthogonally adjacent (decision 32, `LegalityServiceV2.is_adjacent`). The same definition as the designer check; its positive control (entity 18, t42) is in `../designer_check/`.
- Last present threat = the last held tick with a present threat. A project that never had a present threat while held uses its first held tick as the reference and is flagged "never threatened while held" (N counts from adoption). Projects held at the last tick are counted and flagged "open at run end".
- Stale at N = held at some tick >= reference + N, N = 50, 200, 1000. Hp = ratio at the last held tick, per project (last table in `width_tables.md`).
- Dead entity with an open project: not alive at the last log record, with a non-empty current project id; and separately one that still has an ACTIVE project in its project map.

## Answer 3 (width): `width_tables.md` (per-run table, totals, per-project stale table)
Totals over 15 runs per commit:

| commit | runs with any retreat holder | retreat projects | stale N=50 | N=200 | N=1000 | open at run end |
|---|---|---|---|---|---|---|
| a25619971 | 10 of 15 | 26 | 16 | 3 | 0 | 1 |
| d914bace7 | 14 of 15 | 37 | 12 | 4 | 1 | 1 |

- "No living retreat holder at the parent" holds in 5 of 15 parent runs (urban s42 and s44, crowded s46, frontier_living_world s45 and s46); it is not true across seeds. The parent also has retreat projects that outlast their last threat by 200 ticks (crowded_frontier s43: 2 projects on 2 entities; frontier_living_world s44: 1), so the behaviour is not caused by #769.
- Beyond 1000 ticks past the last threat there is exactly one project in all 30 runs: entity 18, urban_political s42 at d914bace7.
- d914bace7 has a holder in more runs (14 of 15 against 10 of 15) and more retreat projects (37 against 26); its N=50 stale count is not higher (12 against 16).

## Answer 4: dead entities with an open project
Totals over 15 runs per commit (per run in `width_tables.md`): a25619971: 368 dead entities, 229 with a non-empty current project, 240 with an ACTIVE project; d914bace7: 379 dead, 235 with a current project, 253 with an ACTIVE project. About 62% of dead entities keep a current project and 65 to 67% an ACTIVE one at both commits; death does not close projects, with or without #769.

## Answers 1 and 2 (entity 18, urban_political s42 at d914bace7, t63-1402; the re-run's logs)
Held ticks t63-1402: 1340. Tally per tick:
- 1273 ticks: no goal-selection call on the entity, so nothing runs and the project is kept. Entity work_kind on those ticks: ENTITY_ACT with no `action` in its payload on 1206, ENTITY_MOVE on 67.
- 67 ticks with a selection call (t82, 102, 122, ... 1402: every 20 ticks):
  - 57: best_candidate RESOLVE_BLOCKER, no existing project of that kind, `has_project_capacity` False (live projects 3 of max 3), `escalated_need_wins` False. `evaluate_project_switch` is not reached: `intelligence.py:1771` (`if not existing and not has_project_capacity(...) and not escalated_need_wins(...)`) returns an empty update.
  - 3: best_candidate RECOVER, same result at the same line.
  - 6: best_candidate COMBAT_RETREAT with an existing project of that kind; `evaluate_project_switch` is called and returns no switch.
  - 1 (t1402): best_candidate FATIGUE.
- No pending committed intention in any call (path (i) is not the cause); best_candidate was never None (path (ii) is not the cause).
- Answer 1: the line is `intelligence.py:1771`. The entity's live project slots are full (3 of max_active_projects 3), so a new RESOLVE_BLOCKER or RECOVER project cannot start, 60 of the 67 calls, and the ordinary switch test is never reached for them. (Whether the retreat project is one of the three live projects was not logged separately; the logged ACTIVE count is 1.)
- Answer 2: at t1402 FATIGUE is the best candidate with the slots equally full, but `escalated_need_wins(entity, FATIGUE)` returns True (src/ai/goals/escalation.py:18, the SURV-07 need escalation), so the gate at line 1771 lets it through. `evaluate_project_switch` (`intelligence.py:1042`) then runs: current project proj_combat_retreat_42 with score 0.0, lock_until 52 (long expired), interruption resistance 0.3 x multiplier 30; the candidate scores 100.47 and switches (`proj_fatigue_1402`). Among the logged terms the 60 calls blocked at line 1771 and the t1402 call differ only in `escalated_need_wins` (False against True).
- Who decides not to call on the other 1273 ticks: the scheduler, `src/engine/scheduler.py` (`_critical_item`, about lines 108-138, and `_throttled`, about line 112: `is_brain and not should_run(state.tick, ent.id, policy.system_cadence.strategic_intelligence)`). An ENTITY_ACT entity with an empty payload counts as an idle act and a brain tick, and the throttle then skips it on all but the cadence ticks, so no work item is made. Consistent with the data (calls every 20 ticks, work_kind ENTITY_ACT), but not measured: the payload being empty (only its action field was logged), whether any wake (`_is_woken` / `_is_need_woken`) occurred, and which policy gave the 20-tick spacing (the model default of the `strategic_intelligence` cadence field is 10).
- Not traced: what the other live projects are, and why the retreat project's own completion never fires. Neither is needed to name the line.

## Planner's verification notes (rpg-planner-ubuntu)

- Recount: an independent script over the raw logs reproduces every total in the Answer 3 and 4 tables, the entity 18 tally, and the re-run's identity with the first run. The width tables themselves were not re-derived row by row beyond the totals.
- Answer 2 reading: `escalated_need_wins` returns True only for HUNGER or FATIGUE kinds (escalation.py:18). For RESOLVE_BLOCKER and RECOVER it is False by code, whatever the entity's state. So the 60 blocked calls and t1402 also differ in best_candidate's kind, not only in the flag. The project ended because a need past its onset became the best candidate.
- Line numbers: `intelligence.py:1771` is at d914bace7. The same gate is at `intelligence.py:1768` on origin/main 6fdfdf555, written with `route.existing`.
- Live against ACTIVE: `is_live_project` counts ACTIVE and SUSPENDED, and the logs show 3 live with 1 ACTIVE. So 2 of the 3 slots are non-ACTIVE live projects, SUSPENDED by that definition; their ids and kinds were not logged. At t1402 the retreat project's status is ACTIVE (sw record), so it is one of the three there.
- Scope of the N counts: "held" means the current project. A retreat project that is ACTIVE but not current is not counted for living entities, so Answer 3 is a lower bound on "still active". Dead entities show such projects exist in the state: dead entities with an ACTIVE retreat project number 4 at a25619971 and 24 at d914bace7.
- N=50 by commit: 16 against 12 mixes definitions. 9 of the parent's 16 and 2 of d914bace7's 12 are "never threatened while held", counted from adoption. Excluding those, it is 7 against 10. All N=200 and N=1000 projects had a threat while held.
- Hp at the end of the stretch: 2 of the 28 N=50 rows end at hp >= 0.5 (crowded_frontier s43 d914bace7 entity 19 at 0.59; urban_political s42 d914bace7 entity 18 at 1.00). The other 26 end at 0.47 or lower.
- Dead records: 2 dead entities per commit have a last dead record earlier than the last tick; not investigated.
- Work kind: 3 of the 67 selection calls log ENTITY_MOVE, read at the rh logging point. Payload and wakes remain unmeasured, so the scheduler explanation stays unmeasured for those ticks too.
