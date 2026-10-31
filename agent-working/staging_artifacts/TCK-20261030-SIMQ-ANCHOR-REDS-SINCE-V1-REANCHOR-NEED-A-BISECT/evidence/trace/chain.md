# Trace pair: a25619971 (parent) vs d914bace7 (#769), urban_political seed 42, 200t

Method: `probe.py` (this directory) is loaded in place of the measure script, from the clean `git archive` of each commit, and wraps `GoalRegistry.get_all_scores`, `scorers.retreat_pull`, `GroupSystem.update_groups`. Wrapper as in the bisect: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, PYTHONHASHSEED=0, audit_mode, main checkout `.venv/bin/python`, MemAvailable 6.0 to 6.2 GB, about 20 s per run. The probe only reads; no src file was edited. Three pairs were run (a probe field added each time); the logged rows common to the pairs were identical between repeats for both commits. `*.key_rows.jsonl` are the rows quoted below.

## (i) The tick-42 difference is decided inside #769's changed path

The whole `src/` diff a25619971..d914bace7 is `CombatRetreatScorer.score` (`src/ai/goals/scorers.py:238-239`, new `if acting_threat_to(entity, state): utility = retreat_pull(utility, hp_ratio)`) and `retreat_pull` (`src/engine/need_pull.py`).

Entity 18, tick 42, at (82,52), hp 20 of 80 (hp_ratio 0.25). Position, hp, navigation and every other goal score are identical in both runs (COMBAT_ENGAGE 67.93, FATIGUE 2.1, GUILD 25, HARVESTING 4.91, HUNGER 2.1, RECOVER 60, REGION_STABILIZATION 100.0 `bandit_road`, RESOLVE_BLOCKER 80, SOCIAL 10, TOWN_RETURN 54.6). The one score that differs:

| | COMBAT_RETREAT utility | how |
|---|---|---|
| a25619971 | 84.5188 | raw: (1-0.25)*100 + panic*50 - bravery*30, no pull |
| d914bace7 | 123.3988 | `retreat_pull(84.5188, 0.25)` is called (acting hostile present, branch taken): +38.88 |

So retreat (84.52) loses to REGION_STABILIZATION (100) in the parent and wins (123.40) in d914bace7. Result, from the per-tick log of entity 18 (ticks 40 to 42 identical, target (80,45)): from tick 43 the parent has project `stabilize`, navigation target (70,50) (inside `bandit_road`, bounds (40,40)-(100,60)); d914bace7 has project `combat_retreat`, target (25,25) (`town_center`). The ACTION_WITHHELD_BY_POSTURE no-ops seen at tick 42 earlier were these two targets. No other call is involved: entity 18's inputs were identical up to tick 42 and `retreat_pull` is the only changed function.

## (ii) Chain from tick 42 to the first group-objective difference

1. t43 on: entity 18 heads west to the retreat target in d914bace7 ((74,59) at t78, (68,59) at t84) and stays near (82,50) in the parent.
2. First group-record difference, t84: group 10006 (leader 18, members 18 and 30, cohesion radius 5.0). Entity 30 is at (83,45) in both. Parent: 18 at (82,50), distance 5, kept. d914bace7: 18 at (68,59), distance squared 421 > (2 x 5)^2 = 100, so the member loop in `GroupSystem.update_groups` (`src/systems/world_systems/groups.py`, the `dist_sq > (group.cohesion_radius * 2)**2` test) drops 18 and 30, fewer than 2 members remain, and 10006 is marked dissolved at t84. In the parent 10006 lives on (leader changes at 106 and 113, reuse below).
3. Different group sets follow: parent forms 10005 at t104 (12,19); d914bace7 forms 10005 at t113 (5,25).
4. First tick where group-objective creation differs, t123: a new group for entities 3 and 28 is formed in both runs. Its id is `10000 + len(state.groups) + len(groups_add_or_update)` (groups.py, formation branch). `state.groups` has 5 records in both; the other updates pending in the same tick are 1 in the parent (the dissolving (5,25) group) and 2 in d914bace7 (that, plus an update of group 10004), so the id is 10006 in the parent (the same id as the group dissolved in that tick) and 10007 in d914bace7. The directive id `group_obj_{group.id}_{member}` therefore differs from t124 (group_obj_10006_3 against group_obj_10007_3). Membership, leader and members of the new group are the same in both runs.

## What this does not show

The id difference at t123 is bookkeeping, not a behavioural change by itself. The behavioural differences that reach the WORLD pillar run through entity 18 (t43 onward: the t84 dissolution, its survival, and its earlier kill at t172 in the parent) and entity 3's later position difference (from t148). Whether entity 3's position change follows from the group-id difference or from other consequences of entity 18's different route is not traced; the ruling limited this pair to a short one. The `len(groups_add_or_update)` id formula is a latent id collision (a new group can take the id of a record dissolved in the same tick); it exists at both commits and is not touched here.
