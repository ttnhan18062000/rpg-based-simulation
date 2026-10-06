---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION
artifact_type: plan
tags: [engine, combat]
---

# Plan

Written retroactively at close: this ticket was hand-orchestrated and the plan was carried in the investigation and commit messages. It records what was actually done, not a prediction.

1. Measure (investigation.md): live lifetimes of target-carrying `ENTITY_MOVE`s, by kind, legacy vs fixed arms.
2. Replace the PURSUE-only `pursuit_reached_attack_range` / `pursuit_completion_update` in `src/engine/candidate_selector.py` with `tracked_move_complete`, `_combat_positioning_kind` (keyed on movement mode and payload reason) and `tracked_move_completion_update`. A dead, inactive or gone target ends PURSUE, INTERCEPT, REPOSITION+BRACKETING, RETREAT+KITING; the in-reach end applies to all but kiting. Guard and cover-seeking untouched.
3. Point both dispatchers (`executor.py`, `worker_logic.py`) at the new helper.
4. Bind `entity_target_objective.py` under `goal_hierarchy` in `registries/mechanisms.yaml`; re-measure the completeness and state-caller pins.
5. Docs: kernel note, tactical contract section 3, divergence 2.70, parity COMB-329 evidence and COMB-331.

Out of scope: the live-tracking helper's mode blindness (filed as TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE) and the group-guard move (TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER).
