---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP
artifact_type: investigation
tags: [combat]
---

# Investigation

## Facts (pinned: governor NORMAL, audit_mode, budget off, LocalSequentialExecutor)

**Cadence.** The live NORMAL policy runs `strategic_intelligence = 10` (`src/engine/policy.py:92`; `k._current_policy.system_cadence` prints it). `GovernorPolicy()` defaults give 1 (`policy.py:29`), which is NOT what the kernel runs: an earlier "cadence 1" claim in this ticket's trace was wrong. An idle entity (`ENTITY_ACT` with an empty payload) gets a brain once every 10 ticks, staggered by entity id (`scheduler.py:81-83`, `cadence.py should_run`). After a held-move interrupt, 159 of 170 entity-ticks (frontier_living_world seed 43) and 12 of 15 (crowded_frontier) had no scheduled item for the entity (task `ENTITY_ACT`, payload empty, readiness at least 100, active), so any "end the move so the brain decides next" path waits up to 10 ticks. LOD does not explain it (`lod.py:35`: a non-empty payload forces LOD 0; 48 of 58 interrupted entities were LOD 0 idle). Open question, not built (perf's area, #415): letting a present threat bring the brain forward is a governor/policy change.

**Movement without a move task.** `pipeline_phases/movement.py:250-275` takes the target from a fresh `target_set`, else `entity.navigation.target`, live-refreshes it through `resolve_live_tracking_target` (:255), and calls `MovementSystem.resolve_move` (:275); the task's `work_kind` is never read. `candidate_selector.select` (about :168-260) also reads only the navigation target and mode. `resolve_live_tracking_target` retargeted onto the entity named by `payload["target_id"]` for ANY task, so an `ENTITY_ACT` ATTACK holder walked toward its attack target's live position. The ATTACK/SKILL emissions (`tactical.py` :770-799) carried a TaskUpdate and no NavigationUpdate, so a target left by an earlier PURSUE or INTERCEPT stayed.

**What `resolve_move` does for an ATTACK holder whose live target is adjacent** (instrumented, frontier_living_world seed 43, 515 calls with an ATTACK task and a live target): target adjacent and the entity still moved 156 (85 without and 71 with an opportunity-attack swing, 30 percent); target not adjacent and moved 258 (closing on the live target with no pursue decision). crowded_frontier 227 calls: adjacent and moved 44 (19 percent). Mechanism (code, not separately instrumented at line level): the live-retargeted destination is the occupied tile of the target; `verify_movement_legality` refuses the step (movement.py:139), the ladder runs `_find_sidestep` (movement.py:54, called at :153), which steps to an orthogonal side tile, off adjacency; the yield branch (:158) can push the occupant instead. The earlier HELD-ATTACK ticket fixed the same sidestep for tracked moves on their completion tick (`_already_settled_this_tick`).

## Change (option 1, per rpg-planner)
Action emissions clear the target (`navigation=NavigationUpdate(target_clear=True)` on ATTACK/SKILL); `resolve_live_tracking_target` follows the target only for entity-tracking moves and never for an entity holding an action task; an entity holding an action task (`ENTITY_ACT` with a payload) is neither offered a move nor moved unless the tick sets a target (`MovementCandidateSelector.holds_action_task`, used in `select` and in the movement phase). Side effect to disclose: an ATTACK holder whose target steps away no longer closes the gap through live tracking (258 of 515 calls did); it closes after OUT_OF_RANGE returns it to the brain, up to 10 ticks later.

# OA fix (option 1) five-seed measurement (seeds 42-46, 1500 ticks, audit_mode, budget off, LocalSequentialExecutor, governor pinned NORMAL)

Arms: main = origin/main 10944422c; fixed = oa-fix (action emissions clear the target; live tracking only for tracking moves; no movement under an action task unless the tick sets a target). Mean (SD) [per-seed 42..46].

## crowded_frontier

| metric | main | fixed |
|---|---|---|
| OA hits | 279.0 (28.4) [286, 240, 263, 314, 292] | 178.6 (27.7) [147, 169, 162, 203, 212] |
| hits: decided this tick | 11.0 (4.3) [9, 17, 7, 14, 8] | 4.8 (1.9) [5, 4, 4, 3, 8] |
| hits: held move | 105.6 (38.4) [123, 37, 122, 122, 124] | 104.6 (6.8) [107, 94, 110, 102, 110] |
| hits: neither | 162.4 (20.5) [154, 186, 134, 178, 160] | 69.2 (27.7) [35, 71, 48, 98, 94] |
| ATTACK decisions | 40.6 (6.2) [46, 41, 30, 42, 44] | 46.8 (12.8) [47, 36, 33, 54, 64] |
| attacks landed (executions ok) | 38.6 (8.9) [49, 36, 26, 37, 45] | 107.4 (32.3) [107, 52, 121, 124, 133] |
| attack executions failed | 34.8 (6.7) [46, 32, 28, 34, 34] | 47.8 (10.8) [42, 42, 44, 44, 67] |
| total deaths | 37.6 (1.5) [39, 35, 38, 38, 38] | 36.4 (1.8) [38, 35, 37, 34, 38] |
| DEFEAT deaths | 19.6 (6.4) [15, 14, 16, 28, 25] | 11.4 (3.0) [7, 12, 13, 10, 15] |
| STARVATION deaths | 11.8 (5.3) [15, 16, 16, 6, 6] | 13.2 (4.4) [20, 15, 12, 10, 9] |
| alive t=1000 | 6.2 (2.2) [8, 7, 8, 3, 5] | 9.2 (4.0) [10, 14, 10, 9, 3] |
| alive t=1100 | 2.8 (1.6) [1, 5, 4, 2, 2] | 4.0 (3.1) [1, 8, 4, 6, 1] |

## frontier_living_world

| metric | main | fixed |
|---|---|---|
| OA hits | 276.2 (62.0) [334, 246, 314, 182, 305] | 123.6 (37.6) [95, 120, 108, 106, 189] |
| hits: decided this tick | 11.6 (1.1) [12, 11, 13, 12, 10] | 8.2 (4.0) [2, 7, 12, 11, 9] |
| hits: held move | 110.4 (51.9) [115, 55, 158, 60, 164] | 78.4 (20.9) [82, 73, 72, 54, 111] |
| hits: neither | 154.2 (39.0) [207, 180, 143, 110, 131] | 37.0 (21.8) [11, 40, 24, 41, 69] |
| ATTACK decisions | 45.8 (26.5) [49, 45, 20, 88, 27] | 62.0 (29.9) [53, 44, 53, 45, 115] |
| attacks landed (executions ok) | 41.8 (23.9) [50, 80, 28, 21, 30] | 190.4 (35.6) [243, 154, 203, 162, 190] |
| attack executions failed | 32.8 (17.4) [44, 58, 20, 22, 20] | 57.0 (4.5) [60, 56, 63, 54, 52] |
| total deaths | 43.2 (2.4) [45, 46, 40, 43, 42] | 41.8 (2.7) [43, 40, 38, 44, 44] |
| DEFEAT deaths | 18.8 (4.9) [24, 11, 20, 18, 21] | 11.0 (4.1) [11, 8, 10, 8, 18] |
| STARVATION deaths | 14.4 (2.2) [12, 18, 14, 14, 14] | 15.4 (3.0) [17, 14, 13, 20, 13] |
| alive t=1000 | 15.4 (2.7) [11, 17, 18, 15, 16] | 19.0 (1.6) [21, 18, 20, 19, 17] |
| alive t=1100 | 13.4 (3.4) [9, 13, 18, 12, 15] | 14.8 (2.9) [14, 13, 20, 14, 13] |

## urban_political

| metric | main | fixed |
|---|---|---|
| OA hits | 135.8 (26.4) [165, 122, 112, 116, 164] | 109.6 (43.9) [114, 95, 52, 174, 113] |
| hits: decided this tick | 4.8 (1.9) [3, 4, 5, 8, 4] | 9.4 (4.6) [12, 3, 15, 7, 10] |
| hits: held move | 26.4 (8.5) [21, 38, 17, 32, 24] | 59.0 (46.1) [82, 15, 15, 123, 60] |
| hits: neither | 104.6 (31.4) [141, 80, 90, 76, 136] | 41.2 (23.0) [20, 77, 22, 44, 43] |
| ATTACK decisions | 28.2 (8.7) [32, 25, 31, 15, 38] | 45.8 (15.4) [23, 51, 49, 41, 65] |
| attacks landed (executions ok) | 23.8 (6.6) [25, 22, 26, 14, 32] | 110.0 (24.7) [109, 99, 126, 76, 140] |
| attack executions failed | 27.6 (11.0) [34, 20, 36, 12, 36] | 41.2 (16.5) [24, 64, 46, 26, 46] |
| total deaths | 23.8 (3.0) [28, 25, 22, 20, 24] | 28.0 (0.7) [28, 28, 28, 29, 27] |
| DEFEAT deaths | 7.6 (5.1) [13, 2, 5, 5, 13] | 10.6 (5.4) [13, 7, 7, 19, 7] |
| STARVATION deaths | 10.8 (2.3) [11, 12, 13, 11, 7] | 10.4 (3.6) [9, 15, 13, 6, 9] |
| alive t=1000 | 12.2 (3.0) [9, 11, 13, 17, 11] | 10.2 (2.7) [10, 10, 13, 6, 12] |
| alive t=1100 | 6.8 (3.5) [2, 5, 9, 11, 7] | 3.2 (2.8) [2, 2, 8, 1, 3] |


## urban_political attribution (pinned, seeds 42-46, main 10944422c vs this change; probe `probes/oa_attr.py`)
Deaths by cause, 5-seed mean main to fixed: total 23.8 to 28.0; DEFEAT 7.6 to 10.6 (+3.0); COMBAT 1.2 to 4.6 (+3.4); STARVATION 10.8 to 10.4; HAZARD 4.2 to 2.4 (-1.8). Per seed (42..46) total deaths main [28, 25, 22, 20, 24] to fixed [28, 28, 28, 29, 27]; DEFEAT main [13, 2, 5, 5, 13] to fixed [13, 7, 7, 19, 7] (seed 45 is +14); COMBAT main [1, 2, 2, 0, 1] to fixed [4, 3, 6, 1, 9]. DEFEAT deaths labelled by the last damage within 5 ticks (5 seeds summed): main 38: neither 22, decided this tick 5, held move 11 (PANIC_RETREAT 5, REGROUP 4, PURSUE 2); fixed 53: held move 30 (REGROUP 20, PURSUE 5, PANIC_RETREAT 3, INTERCEPT 2), decided this tick 17, neither 6. Held-move hits by reason|mode, main to fixed: REGROUP 33 to 147, PURSUE 48 to 71, INTERCEPT 19 to 35, PANIC_RETREAT 9 to 26, BRACKETING 23 to 16. Attack executions that succeeded per seed main [25, 22, 26, 14, 32] to fixed [109, 99, 126, 76, 140]. Why held REGROUP moves became more common was not traced; follow-up ticket TCK-20261008-A-HELD-REGROUP-MOVE-WALKS-INTO-PERCEIVED-HOSTILES-AND-IS-NEVER-RE-DECIDED.

## Melee legality check (requested on #424; merged code, seeds 42-46)
ATTACK decisions at whole-tile distance 2 or more: frontier_living_world 69 of 228 and crowded_frontier 12 of 167, every one with attacker range 3; with range 1: 0.
