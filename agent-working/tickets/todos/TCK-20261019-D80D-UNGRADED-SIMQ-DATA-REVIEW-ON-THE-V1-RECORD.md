---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-D80D-UNGRADED-SIMQ-DATA-REVIEW-ON-THE-V1-RECORD
phase: open
date: 2026-10-19
tags: [observability]
---

# TCK-20261019-D80D-UNGRADED-SIMQ-DATA-REVIEW-ON-THE-V1-RECORD

## Title
The first SimQ deliverable is an ungraded end-to-end data review of the v1 record (D80 D)

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Decision 80 (D). The review is the before-picture that D73 and every later repair are read against (memo row 82). It runs after D80C and baseline v1.

## Scope
- From the v1 runs' lossless files (3 gate worlds, seeds 42-46): counts per event type.
- The types that never fire, compared with the D80 A inventory.
- A schema check of each type against the typed record the catalog names.
- For each world, whether the events explain the end state (deaths by cause, coin, population).
- The output is a report with no grade.

## Out of Scope
- Grades (D77).
- Content tuning to make a type fire (D33; memo row 82 guard 2).

## Acceptance Criteria
- The report is committed under stored_artifacts and cites the v1 sha.
- Every never-fired type is matched to a v1_disclosure row, or a new row is proposed to rpg-designer.
- Nothing in it is called a grade.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (must land first)
- TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK, TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE, TCK-20261019-D80D-UNGRADED-SIMQ-DATA-REVIEW-ON-THE-V1-RECORD (order B, C, D, then D73)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (testing)

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md rows 77, 80, 82 (82 on rpg-designer-after-v1 ff0a4a9df until it merges)
- docs/plans/systemic_world/v1_disclosure.md (E, Q sections)

## Related Stored Artifacts
- none

## Related Code Areas
- src/simulation_quality/
- the D80 A event catalog

## Assumptions / Open Questions
- Order and guards per memo row 82 (rpg-designer, user-confirmed 2026-10-19). B, C and D73 may share batch 1 under the PR size rule, each as its own measured step.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
