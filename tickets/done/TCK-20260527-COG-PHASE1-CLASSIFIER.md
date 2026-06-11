---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260527-COG-PHASE1-CLASSIFIER
phase: done
date: 2026-05-27
tags: [cog, phase1, classifier]
---

# TCK-20260527-COG-PHASE1-CLASSIFIER

## Title

Implement Phase 1 Route-Family Classifier

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a RouteFamilyClassifier that consumes action and intent traces to group low-level raw actions into strategic route families (e.g., buy_upgrade, craft_upgrade, ask_information, recover, defer_with_reason).

## Scope

- Create `RouteFamilyClassifier` under `src/testing/route_family_classifier.py`.
- Support mapping raw intents/actions to Phase 1 route-families.
- Add unit tests under `tests/unit/strategic/test_classifier.py`.

## Out of Scope

- Implementing the performance budget gates (Task 10).

## Acceptance Criteria

- Classifier successfully detects route families from trace logs.
- Detects multiple route families in one execution run.
- Detects forbidden patterns (repeated failed actions, hidden knowledge usage).
- Unit tests pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Task 9)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/testing/route_family_classifier.py`
- `tests/unit/strategic/test_classifier.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Implemented `RouteFamilyClassifier` supporting trace log matching to route families.
- Added pattern detection for consecutive failed attempts (`infinite_same_failed_action`) and untrusted secret node gathering (`omniscient_hidden_source`).

## Test Summary

- Run `pytest tests/unit/strategic/test_classifier.py` verifying basic classification, defer reason parsing, and consecutive/omniscient forbidden pattern detections.
- All 4 tests pass successfully.

## Files Changed

- `src/testing/route_family_classifier.py`
- `tests/unit/strategic/test_classifier.py`

## Completion Summary

- RouteFamilyClassifier fully implemented, verified, and passing all unit tests. Tracing classification is now production-ready for E2E scenarios.

