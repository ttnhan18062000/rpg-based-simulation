---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP
phase: open
date: 2026-10-31
tags: [social, simulation-quality]
---

# Investigation: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP

Checked on origin/main 6fdfdf555. Findings (a)-(c) only; no code written.

## (a) What makes a count collide with a live id
`src/systems/world_systems/groups.py:308`: `new_g_id = 10000 + len(state.groups) + len(groups_add_or_update)`.
- Nothing shrinks `state.groups` in the running pipeline. `groups_remove` has no non-empty producer in `src/` (only the merge in `pipeline_phases/groups.py:58` and `updates.py:1256`); dissolution keeps the record with `dissolution_tick` set (l.110, l.170). So the collision needs no removal.
- `groups_add_or_update` also holds in-place updates of existing groups (dissolution markers l.110/l.170, the cohesion update l.227). Each one adds 1 to the id without adding a record. Ids therefore run ahead of the record count (gaps). Later, the count falls below the highest live id and `10000 + count + k` lands on it.
- Apply overwrites silently: `src/engine/apply_plan.py:123` `new_groups[g.id] = g`. Within one tick `pipeline_phases/groups.py:48-53` also replaces a same-id row with the later one.
- Repro (`repro_collision.py`, venv python, PYTHONHASHSEED=0): groups {10000 dissolved, 10001 dissolved, 10004 live (members 11,12)}, tick 10, ungrouped 1,2 with an active recruitment contract. update_groups emits `(10004,[11,12])` then `(10004,[1,2])`. After apply: groups = {10000:[99], 10001:[98], 10004:[1,2]}. The live group's record is gone.

## (b) Where the overwritten members point afterwards
Measured in the same repro: entities 11 and 12 keep `identity.group_id == 10004`. 10004 is now a record whose members are {1,2}, leader 1; 11 and 12 are not in it. One more update_groups tick on that state emits only `(10004,[1,2])` and no `group_id_set` for 11/12, so nothing clears them. They stay non-None, so formation (`group_id is None` filter) never takes them again: ghost members until they die. Not shown: how often this happens on the real worlds (the planner's group_upd rows t106/t113/t123 are update rows, not the applied store).

## (c) Other sites that mint group ids
- `src/engine/military_conflict.py:341`: `stable_int31(contested_region_id, attacker_id, tick)` (faction squad, divergence 2.141). Not a count. It can only repeat for the same region, attacker and tick, and one squad is made per region per tick. A clash with the 10000-block is possible only by chance. Not the same defect.
- `src/domains/cooperation/phase.py:213` and `pipeline_phases/groups.py` only copy or merge rows. No other `GroupRecord(` constructor in `src/` outside `core/state.py`.
- So `groups.py:308` is the only count-based minter.

## Not shown / notes
- Open remote branches touching these files: `batch-cognition-hazard-group-dissolution-raid-mob` and `semantic-entity-index-epic` (the latter changes `military_conflict.py` by 37 lines). I did not read them for group id changes.
- No fix shape chosen. Planner's candidate (max over all retained ids + ids pending this tick + 1, counter as typed state if used) awaits the designer.
