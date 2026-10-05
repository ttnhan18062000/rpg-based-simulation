---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES
artifact_type: plan
tags: [strategy, cognition, combat]
---

# Plan: typed entity target and a real lifecycle

Representation (the planner ruled the direction, not the shape): a new typed field, not a target union.
`ObjectiveState.target_entity_id: Optional[int] = None` and `GoalScore.target_entity_id: Optional[int] = None`.
`target` (the string) is unchanged for every existing consumer, including `ObjectiveIntentResolver`'s
`ATTACK_TARGET`.

1. `src/core/strategic.py`: add the field to `ObjectiveState` (contested surface; hold requested from the
   planner). `src/core/state.py`: omit it from the canonical dict when `None`.
2. `src/ai/goals/base.py`: field on `GoalScore`. `src/ai/goals/scorers.py`: `CombatEngageScorer` sets it.
   `src/ai/score_modifiers.py`: `dataclasses.replace` instead of a lossy field-by-field rebuild.
3a. New `src/systems/strategic_systems/entity_target_objective.py` holds the pure predicate
   (`entity_target_outcome`, `ENTITY_TARGET_PERCEPTION_RADIUS`) shared by the strategic pass and
   `work_queue.py`, which schedules an entity-targeted objective whose target ended as a tier-3 transition
   (an ACTIVE project is otherwise only evaluated when dirty or on the sweep). Added after the first A/B
   showed the hook fired too late.
3. `src/systems/strategic_systems/intelligence.py`: copy it into the objective at creation (generic branch),
   set it for a resumed `COMBAT_ENGAGE` committed intention, and add the termination in the lifecycle block:
   target dead -> `RESOLVED`/`COMPLETED`; target gone or beyond the perception radius (10, Manhattan, the
   radius `CombatEngageScorer` chooses within) -> `FAILED`/`ABANDONED`.
4. `src/engine/tactical.py::_resolve_target_position`: a typed entity target resolves to the **live**
   position (dead or missing: no position, no stale fallback); every untyped objective takes the existing
   path unchanged.
5. Docs: `tactical_contract.md` §7, divergence §2.67, parity entry, ticket.

Scope guards: no `SocialContractScorer` change (second live case, reported to the planner); no change to
`ProjectState.kind`, scorer weights or combat volume; no bounded give-up cap.
