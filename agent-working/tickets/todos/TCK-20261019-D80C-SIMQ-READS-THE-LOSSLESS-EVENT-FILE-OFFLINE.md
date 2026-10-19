---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE
phase: open
date: 2026-10-19
tags: [observability]
---

# TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE

## Title
SimQ reads the run's lossless simulation_events.jsonl offline, never the live stream (D80 C)

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Decision 80 (C). The live stream (redis or in-process) is sampled under queue pressure, so scores depend on host speed (v1_disclosure Q3). The lossless file is EventRecorder's simulation_events.jsonl (src/observability/event_recorder.py:103; TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER, #645). This is step 2 after v1, following D80B.

## Scope
- An offline SimQ entry point that takes a run dir and replays its simulation_events.jsonl through the scorers.
- The calibration and compare tools use it.
- The live dashboard stream stays display-only.
- Per-type event counts are an output, because memo row 82's per-repair criterion reads them.

## Out of Scope
- Grades (D77).
- The observer hook (D80B).

## Acceptance Criteria
- The same run dir gives a byte-identical report on two hosts, or under artificial load.
- The run_determinism sidecar is honoured (#649).
- A run without the lossless file is refused.
- The simulation hash is identical to v1.

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
- src/observability/event_recorder.py
- src/simulation_quality/
- tools/ (calibrate_simq, simq compare)

## Assumptions / Open Questions
- Order and guards per memo row 82 (rpg-designer, user-confirmed 2026-10-19). B, C and D73 may share batch 1 under the PR size rule, each as its own measured step.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
