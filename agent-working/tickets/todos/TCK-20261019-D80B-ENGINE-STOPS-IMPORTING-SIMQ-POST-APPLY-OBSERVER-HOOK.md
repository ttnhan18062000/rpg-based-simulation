---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK
phase: open
date: 2026-10-19
tags: [observability]
---

# TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK

## Title
The engine stops importing SimQ: a generic post-apply observer hook replaces kernel.py's SimQ hub wiring (D80 B)

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Decision 80 (B). The kernel builds SimQ itself: src/engine/kernel.py:230-272 imports src.simulation_quality (the feed, QualityHub, ScoringWeights, QualityPersistence, build_all_scorers), wires `quality_fn=_hub.on_envelope` into EventRecorder, and stops it and reads the report at about 1148-1167. This is step 1 after baseline v1, under memo row 82.

## Scope
- A typed observer registry that the kernel calls after authoritative apply. The kernel knows no observer types.
- SimQ registers from outside src/engine, at the composition root (API or run harness).
- Move the RunLedger onto the same hook if that fits without changing its output.
- Add an import-linter contract: src.engine must not import src.simulation_quality.

## Out of Scope
- How SimQ reads events (D80 C).
- Any change to scorers or grades (D77).

## Acceptance Criteria
- The final hash is identical to the v1 record on 3 gate worlds x seed 42, with observability ON and OFF.
- The new lint-imports contract passes.
- The SimQ report is unchanged on one calibration run.
- Paired numbers are recorded as their own step (memo row 82).

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
- src/engine/kernel.py (230-272, 1148-1167)
- src/observability/event_recorder.py (quality_fn)
- src/simulation_quality/
- importlinter config

## Assumptions / Open Questions
- Order and guards per memo row 82 (rpg-designer, user-confirmed 2026-10-19). B, C and D73 may share batch 1 under the PR size rule, each as its own measured step.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
