---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED
artifact_type: plan
tags: [combat, bug]
---

# Plan

1. Detect arrival in `MovementSystem.resolve_move`: the step onto the walk's own destination tile is rejected with `path_not_found` or `building_obstruction` AND the rejected step equals the destination tile AND the entity is orthogonally adjacent (MOV-07). Return `target_clear` and nothing else.
2. Tests: the arrival cases and their exclusions (obstacle on the way, diagonal, entity on the destination), a walker loop that must stop jittering, and the tactical dispatch of `REST` after arrival.
3. Measure before and after on one tree (the capacity-fix tree vs this branch) for the two worlds, and count arrivals by target kind across all 24 worlds.
4. Out of scope: the scheduler, the yield push, `core_actions.py`, `town_resolution.py`, the stored project score, the priority of biological needs.
