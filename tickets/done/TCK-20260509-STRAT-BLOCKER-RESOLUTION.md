---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260509-STRAT-BLOCKER-RESOLUTION
phase: done
date: 2026-05-09
tags: [strat, blocker, resolution]
---

# TCK-20260509-STRAT-BLOCKER-RESOLUTION

## Title

Implement missing resolution logic for 'access' and 'inventory' blockers

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

The StrategicIntelligenceSystem.resolve_blockers method only resolves 'material' blockers. 'access' blockers (navigation failures) and 'inventory' blockers (capacity failures) are currently never resolved once generated, causing entities to stay in a blocked state even after reaching their destination or clearing inventory.

## Scope

- Implement resolution logic for 'access' blockers in `StrategicIntelligenceSystem.resolve_blockers`.
- Implement resolution logic for 'inventory' blockers in `StrategicIntelligenceSystem.resolve_blockers`.
- Ensure `test_access_blocker_resolution` passes.

## Out of Scope

- Refactoring the entire strategic system.
- Changes to other blockers kinds not mentioned.

## Acceptance Criteria

- `tests/engine/test_phase6_strategic_cognition.py` passes.
- Entities correctly mark 'access' blockers as resolved when reaching the target location.
- Entities correctly mark 'inventory' blockers as resolved when capacity becomes available.

## Related Tickets

- None

## Related Docs

- `docs/superpowers/specs/2026-04-26-validation-pipeline-design.md` (likely context for validation)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/systems/strategic.py`
- `tests/engine/test_phase6_strategic_cognition.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Use distance check for 'access' blockers.
- Use capacity check for 'inventory' blockers.

## Test Summary

- Run `pytest tests/engine/test_phase6_strategic_cognition.py`

## Files Changed

- `src/systems/strategic.py`

## Completion Summary

- TBD
