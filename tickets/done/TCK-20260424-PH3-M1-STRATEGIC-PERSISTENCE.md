# TCK-20260424-PH3-M1-STRATEGIC-PERSISTENCE

## Title
Phase 3 Milestone 1: Strategic Objective Persistence

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement long-term strategic goal setting and objective persistence to prevent tactical jitter and ensure entities follow through on non-combat projects.

## Scope
- Implement a `StrategicIntelligenceSystem` hook to propose and manage projects (e.g., Harvesting).
- Implement "Project Locking" to prevent entities from abandoning goals too easily.
- Support "Suspend/Resume" lifecycle for projects interrupted by combat.
- Update `TacticalDecisionSystem` to prioritize strategic objectives over idle exploration.

## Out of Scope
- Group-level strategic coordination (Phase 3 Milestone 2).
- Complex multi-stage craft projects.

## Acceptance Criteria
- [x] Entities identify a resource node and create a locked "Harvesting" project.
- [x] Entities stick to the harvesting goal even if minor distractions occur.
- [x] Entities suspend harvesting if attacked, but resume it once the threat is resolved.

## Related Tickets
- TCK-20260424-PH2-M5-ECONOMY-SCARCITY (Done)

## Related Code Areas
- `src/systems/strategic.py`
- `src/engine/tactical.py`
- `src/engine/domain_logic.py`
- `src/engine/scheduler.py` (Fixed active entity check)

## Implementation Notes
- Implemented `StrategicIntelligenceSystem.evaluate_strategic_intent` for project proposal/resumption.
- Added project status tracking (`ACTIVE`, `SUSPENDED`, `COMPLETED`).
- Hardened the `DeterministicScheduler` to prevent inactive (dead) entities from executing brain logic.
- Resolved parity test regressions in combat resolution and readiness recovery.

## Test Summary
- `tests/parity/test_strategic_persistence.py`: 2 passed (Project Persistence, Combat Interruption).

## Files Changed
- `src/systems/strategic.py`
- `src/engine/tactical.py`
- `src/engine/domain_logic.py`
- `src/engine/scheduler.py`
- `src/engine/pipeline.py`
- `tests/parity/test_strategic_persistence.py`

## Completion Summary
Successfully implemented the core strategic project lifecycle. Entities now exhibit purposeful behavior by committing to long-term goals (e.g., harvesting) and correctly handling tactical interruptions (combat) without losing project state. Fixed a significant scheduler bug that allowed dead entities to persist in the execution loop.
