# TCK-20260418-MOV-CONGESTION

## Title

Milestone 3: Congestion & Advanced Anti-Oscillation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implementing advanced movement anti-oscillation logic and hardening edge-case congestion handling (blocked retreat, pursuit collisions, corridor contention).

## Scope

- Implement rhythmic oscillation detection in `MovementModel`.
- Add reroute penalty/hysteresis to prevent Path A/B flip-flopping.
- Implement coordinated yielding for blocked retreat/pursuit lanes.
- Add regression scenario suite for complex congestion patterns.

## Out of Scope

- Multi-actor group pathfinding (A* with multiple goals).
- Dynamic terrain modification (e.g., digging).

## Acceptance Criteria

- [x] Rhythmic oscillation (A-B-A) is detected and suppressed after 3-4 cycles.
- [x] Reroute flip-flopping is minimized via route commitment memory.
- [x] High-priority (RETREAT) entities successfully force yields from allies.
- [x] Corridor contention is resolved without pass-through.
- [x] 100% pass rate on `tests/movement/test_congestion_milestone_3.py`.

## Related Tickets

- None

## Related Docs

- [combat_movement_updated.md](file:///home/vboxuser/Work/rpg-based-simulation/combat_movement_updated.md)

## Related Stored Artifacts
- [plan.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-MOV-CONGESTION/plan.md)
- [plan_task.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-MOV-CONGESTION/plan_task.md)

## Related Code Areas

- `src/core/logic/movement_model.py`
- `src/core/aspects/mind.py` (NavigationState)
- `src/actions/base.py` (NavigationUpdate)

## Assumptions / Open Questions

- We assume 3 cycles is a suitable threshold for "oscillation".
- We assume `INTENTION_PRIORITY` is the primary arbiter for yielding.

## Implementation Notes

- Will use `pos_history` to track movement patterns.
- Will extend `NavigationState` with `route_fidelity` or similar.
