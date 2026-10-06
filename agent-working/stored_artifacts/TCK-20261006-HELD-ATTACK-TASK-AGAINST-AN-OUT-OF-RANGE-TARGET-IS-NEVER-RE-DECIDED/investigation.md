---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED
artifact_type: investigation
tags: [combat, cognition]
---

# Investigation

Probes in `probes/`. Config: seed 42 (campaign also 1337), `PROD_SMALL` with `max_tick_budget_ms=1e9`, `no_frame_pacing`, `no_replay`, `audit_mode`, `LocalSequentialExecutor`; each arm twice, every counter identical across runs. Before = `7f361ee73` (origin/main after #378), after = this branch.

## 1. Where out-of-range attacks come from (`atk_origin.py`, on `7f361ee73`)
All 278 `OUT_OF_RANGE` `execute_attack` calls were from held tasks (`crowded_frontier` 4, `frontier_living_world` 274); decision-tick calls were all successes (14). The few ATTACK decisions at a float distance above 1 are fractional positions that `LegalityServiceV2.get_manhattan_dist` accepts through `int()` truncation (1.72 to 1); legality said LEGAL for every one. So the tactical pass does not emit an out-of-reach ATTACK; the hole is the held task.

## 2. The held loop (`trace49.py`, earlier ticket)
Entity 49 at (64,41), target 18 at (65,42), both static from tick 242: melee reach is Manhattan <= 1, the pair is diagonal, every swing is `OUT_OF_RANGE` (-50 readiness), `actions.py` kept the task and `scheduler.py:68` re-runs the brain only for an empty payload, so one swing per ~5 ticks. The two lines contradicted each other.

## 3. The second root cause (`diag_*.py`)
After the clear, the constructed diagonal pair still did not strike in 60 ticks, held or fresh, map-less or in a compiled world. Trace: the pursuer steps orthogonally adjacent (tick 10); on tick 11 `tracked_move_complete` is True and the completion update clears the navigation target, yet `route_movement_intent` read the tick-start target (`entity.navigation.target`, line ~236) and stepped the entity off adjacency (opportunity attack, hp -4), after which it waited a whole cadence. Harness pitfalls found on the way and fixed in the probe, not in `src`: a 500 hp target made the attacker's combat posture withhold the attack (`ACTION_WITHHELD_BY_POSTURE`), so the attacker is made clearly stronger; the target is pinned each tick because the yield push and the target's own movement otherwise confound the geometry.

## 4. Constructed pair, first strike tick (`diag_kernel_strong.py`, 60 ticks)
Before both fixes: fresh 39. With both fixes: held 19, fresh 19. Bound: two brain cadences = 20 ticks.

## 5. Corpus before and after (`corpus_probe.py`, `oor_streak.py`)
See the ticket's Implementation Notes and divergence 2.74. Longest consecutive `OUT_OF_RANGE` run per entity: 4 / 258 to 2 / 2. Campaign deliberate-attack xfail unchanged (still XFAIL, no flip).
