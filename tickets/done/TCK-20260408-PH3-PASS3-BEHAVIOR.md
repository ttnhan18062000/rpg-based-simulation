# Ticket TCK-20260408-PH3-PASS3-BEHAVIOR

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement Behavioral Integration for Phase 3 Lived-Structure. Make entities follow their seeded routines and favor their place attachments in AI decision making. Integrate small-group coordination (cliques) into goal selection.

## Scope
- Routine evaluation and disruption logic in `AIBrain` or `RoutineService`.
- Bias scoring in Utility AI for `RoutineProfile` windows.
- Bias scoring for `PlaceAttachment` locations (Home, Workplace).
- Basic group coordination logic (follow leader, shared targets) for entities in the same `cluster_id` or `group_id`.

## Out of Scope
- Full squad tactics.
- Complex pathfinding for specialized routines (just use existing navigation).
- Inheritance and succession (deferred to Phase 4).

## Acceptance Criteria
- [x] Entities prioritize routine goals (e.g. SLEEP, WORK) during their scheduled hours.
- [x] Entities prioritize their `HOME` location when a `REST` or `SLEEP` goal is selected.
- [x] Entities in the same `cluster_id` show increased likelihood of assisting each other or selecting similar goals when nearby.
- [x] Routines are suppressed when `panic` or `danger` thresholds are exceeded.
- [x] Integration tests verify routine-driven behavior.

## Related Tickets
- `TCK-20260408-PH3-PASS2-SPAWN-ANCHOR` (Done)

## Related Docs
- `phase_3_ds_implementation_plan.md`
- `ds_hl_implementation_plan.md`

## Status
DONE
