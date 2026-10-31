# Trace pair: a25619971 (parent) vs d914bace7 (#769), urban_political seed 42, 200t

Method: `probe.py` (this directory) is loaded in place of the measure script, from the clean `git archive` of each commit, and wraps `GoalRegistry.get_all_scores`, `scorers.retreat_pull`, `GroupSystem.update_groups`. Wrapper as in the bisect: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, PYTHONHASHSEED=0, audit_mode, main checkout `.venv/bin/python`, MemAvailable 6.0 to 6.2 GB, about 20 s per run. The probe only reads; no src file was edited. Four pairs were run (a probe field added each time), plus the planner's own pair in `planner_verify/`; the logged rows common to the pairs were identical between repeats for both commits. `*.key_rows.jsonl` are the rows quoted below.

## (i) The tick-42 difference is decided inside #769's changed path

The whole `src/` diff a25619971..d914bace7 is `CombatRetreatScorer.score` (`src/ai/goals/scorers.py:238-239`, new `if acting_threat_to(entity, state): utility = retreat_pull(utility, hp_ratio)`) and `retreat_pull` (`src/engine/need_pull.py`).

Entity 18, tick 42, at (82,52), hp 20 of 80 (hp_ratio 0.25). Position, hp, navigation and every other goal score are identical in both runs (COMBAT_ENGAGE 67.93, FATIGUE 2.1, GUILD 25, HARVESTING 4.91, HUNGER 2.1, RECOVER 60, REGION_STABILIZATION 100.0 `bandit_road`, RESOLVE_BLOCKER 80, SOCIAL 10, TOWN_RETURN 54.6). The one score that differs:

| | COMBAT_RETREAT utility | how |
|---|---|---|
| a25619971 | 84.5188 | raw: (1-0.25)*100 + panic*50 - bravery*30, no pull |
| d914bace7 | 123.3988 | `retreat_pull(84.5188, 0.25)` is called (acting hostile present, branch taken): +38.88 |

So retreat (84.52) loses to REGION_STABILIZATION (100) in the parent and wins (123.40) in d914bace7. Result, from the per-tick log of entity 18 (ticks 40 to 42 identical, target (80,45)): from tick 43 the parent has project `stabilize`, navigation target (70,50) (inside `bandit_road`, bounds (40,40)-(100,60)); d914bace7 has project `combat_retreat`, target (25,25) (`town_center`). The ACTION_WITHHELD_BY_POSTURE no-ops seen at tick 42 earlier were these two targets. No other call is involved: entity 18's inputs were identical up to tick 42 and `retreat_pull` is the only changed function.

## (ii) Chain from tick 42 to the first group-objective difference (corrected after rpg-planner-ubuntu's verification)

Group objectives issued by `GroupSystem.update_groups` (planner_verify/, read-only probe, same wrapper): the two runs are identical for ticks 0 to 62 (146 rows), and the first difference is **t63**.

1. t42: retreat wins in d914bace7 (see (i)). Entity 18's project `proj_combat_retreat_42` is created at t42 and is entity 18's current project from t43 (per-tick rows t43 to t52, target (25,25)); by t53, the first row of the later project log, it is SUSPENDED and the current project id is empty (so is every `project_stabilize_*` project, in both runs), and it stays SUSPENDED through t62; at **t63 it is ACTIVE and is entity 18's current project again**. The tick at which it went from current to SUSPENDED lies between t52 and t53 and was not logged separately. The parent has no combat_retreat project at all in t53 to t70, and its current project id is empty throughout. Both runs move to (82,60) at t63; the parent is back at target (80,45) by t70, d914bace7 goes on to (25,25).
2. **First difference, t63:** group 10006 (leader 18, member 30) formed at t61 with the same id in both runs. Because the leader now has a current project, `update_groups` (Domain 7 directive propagation) issues `group_obj_10006_30` with target COMBAT_RETREAT to entity 30 every tick t63 to t83 (21 rows). The parent issues no objective to entity 30 at all. Member 30's trust in 18 is 0.5 (>= 0.3) in both runs, so the trust gate is not the difference.
   Why the parent has no project at t62 although its retreat score is 136.45 against REGION_STABILIZATION 100: shown only as far as the state. The parent never creates a retreat project (the t42 pull is what made one in d914bace7). Why the arbitration does not materialise one at t62 in the parent is not traced; it sits in the project-switch arbiter in `intelligence.py` and was not followed (short pair).
3. **t84, group record difference:** `update_groups` measures each non-leader member against `group.anchor` (groups.py cohesion check), not against the leader. The anchor is the mean of the kept members at the previous tick's update (`last_updated_tick` = t-1 in every logged row). In d914bace7 entity 18 walks west while 30 stays at (83,45), so the squared distance to the anchor (equal for both members, as the anchor is their midpoint) is 69.25 at t78, 91.25 at t82, 98.0 at t83 and 105.25 at t84; the limit is (2 x cohesion radius 5)^2 = 100, so 30 is dropped at t84 (only 30: the member loop skips the leader, which is seeded into `new_member_ids` at groups.py:124-128, so the leader is never cohesion-tested), fewer than 2 members remain, and 10006 is marked dissolved. Parent: 6.5 at t84, group kept. (Member-to-member squared distance, 421 at t84, is not the trigger: it was already 277 at t78 and did not fire.)
4. **First id split, t104:** the pair (12,19) forms a group at t104 as id 10005 in the parent (4 records in `state.groups` + 1 pending update, the still-live 18/30 group) and as id 10004 in d914bace7 (4 + 0 pending, since 18/30 was dissolved at t84; 10004 is an old dissolved record that gets overwritten). This is the direct link from the t84 dissolution to the later ids.
5. **t123:** a new group for entities 3 and 28. Id = `10000 + len(state.groups) + len(groups_add_or_update)`: `state.groups` has 5 in both; pending updates are 1 in the parent and 2 in d914bace7, so 10006 (parent) and 10007 (d914bace7). 10006 is entity 3's group id only in the parent; its directive id is `group_obj_10006_3` there and `group_obj_10007_3` in d914bace7 from t124. t124 is a later consequence of the t63 and t84 differences, not the first difference.

## Observed lead, not traced

Entity 3's group objective runs t124 to t143 in the parent and t124 to t199 in d914bace7 (planner_verify rows), and the vanished `hazard_drain_applied` events are entity 3 at t185 to t189. That the id difference is "bookkeeping only" is therefore NOT established; no claim either way. Entity 3's position difference (from t148) is likewise not traced to a cause.

## Planner verification

`planner_verify/` holds rpg-planner-ubuntu's own read-only probe and its two jsonl outputs (every GROUP_OBJECTIVE issued by `update_groups`, same wrapper). They confirmed (i) (`retreat_pull` at hp ratio 0.25 = 60 x smoothstep(0.6, 0.85, 0.75) = 38.88; t42 is the earliest call where the pull changes a score; `scorers.py:239` is its only caller) and the t123 id arithmetic, and found the t63 first difference, the anchor measurement and the t104 split that an earlier version of this file got wrong.
