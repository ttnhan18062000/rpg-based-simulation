---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER
artifact_type: investigation
tags: [engine, combat]
---

# Investigation: does a group guard move outlive its leader?

## 1. The mechanism (read from code)

`tactical.py` section 4.1 creates `ENTITY_MOVE` + `MovementMode.GUARD` + reason `CONTRACT_OBLIGATION_GUARD` + `target_id` = leader, only when the mover has a group, the leader is alive and interacting, no hostiles are present and its role is VANGUARD or PROTECTOR. A second guard, reason `GUARDING_ALLY` (section near line 637), guards a wounded ally. The movement phase `continue`s when the entity is at its target and **does not clear the task** (`movement.py` around 262), so arriving never ends a move; only `tracked_move_complete` (gate 4) can, and it did not track `GUARD`. A live mover therefore stands on the move until something re-decides it, which for an `ENTITY_MOVE` nothing does.

## 2. Measurement (probes/guard_move_lifetimes.py; 4 worlds x 2 runs; seed 42, 2000 ticks, audit_mode)

| arm | guard moves | notes |
|---|---|---|
| legacy (pre-gate-4 completion logic, run on this tree; `probes/guard_legacy_arm.log`) | **1**, `urban_political`, both runs identical | `CONTRACT_OBLIGATION_GUARD`, held 1004 ticks, leader 8 dead at tick 1003; **mover 24 was already dead** (`mover_was_dead_at_last_sighting` 1); live-mover ticks with a dead leader **0**; with the group gone **3**; with the leader not interacting 0 |
| after (this change; `probes/guard_after_arm.log`) | **0** in all 8 runs | trajectories diverge once entities are freed, so the one legacy instance does not recur |

The pre-gate-4 current-tree arm (before this change, gate 4 only) also shows 0 guard moves in all 8 runs.

**What the corpus cannot show.** The only instance had a dead mover, so there is no live-mover harm in this corpus, and no per-move before and after. The earlier handover note ("16 live ticks in two worlds") is **not reproduced** by this probe; it came from a different run and is not used as evidence. The defect is real by construction (section 1) and rests on that plus the unit tests.

## 3. Decision: the end condition

The guard's preconditions at decision time are: same group, leader alive, leader interacting. The move ends when its obligation is gone:
- leader dead, inactive or gone: all guard kinds;
- mover ungrouped or in another group: `CONTRACT_OBLIGATION_GUARD` (the obligation is the group role);
- **not** on the leader merely not interacting: INTERACT runs have gaps of up to 11 ticks (`TCK-20261005-ACTION-HANDLERS...` probe, value over 4 worlds x 2 runs), so ending on a pause would make hirelings flap between guarding and re-deciding, and no harm from that case was observed (0 ticks);
- **not** on reach: a guard holds position beside its target.

`GUARDING_ALLY` has the same structure and is included for the dead-ally end only; it has 0 corpus moves, so it is covered by a constructed test and flagged as unmeasured.

## 4. Controls

Guard kinds disabled: exactly 5 tests fail. Group condition disabled: exactly 1 fails.

## 5. Limits

- No live-mover harm was observed; the fix is justified structurally.
- Whether ending on "leader not interacting" would be better is a design question, left open on measured evidence (no harm observed, flapping risk).
- The measurements were taken with the cwd set to this worktree. A first attempt from another worktree crashed (`KeyError: stone_outcrop`), because content seeds from the cwd-relative `data/content`; those logs were discarded.
