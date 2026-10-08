---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP
artifact_type: plan
tags: [combat]
---

# Plan

1. Instrument first, read-only (pinned): which code path moves an entity whose task is `ENTITY_ACT`, what `resolve_move` does when the live target is adjacent, and why an idle entity gets no tactical decision after a held move ends. Result: movement runs on `navigation.target` whatever the task; live tracking retargets for any task with a `target_id`; ATTACK/SKILL emissions leave the target; the live NORMAL policy runs `strategic_intelligence = 10`.
2. Option (1), ruled by rpg-planner (no scheduler, policy or cadence change):
   - ATTACK and SKILL emissions in `tactical.py` carry `NavigationUpdate(target_clear=True)`.
   - `MovementCandidateSelector.resolve_live_tracking_target` follows `payload["target_id"]` only for entity-tracking moves and never for an entity holding an action task.
   - `MovementCandidateSelector.holds_action_task` and the shared `movement_target` rule: an action holder is neither offered a move (`select`) nor moved (`route_movement_intent`) unless that tick sets a target. Errand walks (navigation-only WANDER) and entity-tracking moves are unchanged.
3. Measure pinned on five seeds and three worlds, hits by class, deaths, alive counts, chase convergence; attribute the `urban_political` rise; report, do not tune.
4. Parity: Bible 02 section 7 bullet, ledger COMB-338, divergence 2.84 (Bug Fix).

Out of scope: CONFLICT-04 (the brain path), the held `REGROUP` move ticket, Lane B's held INTERACT, the opportunity-attack rule, anything in scheduler, kernel, governor or policy.
