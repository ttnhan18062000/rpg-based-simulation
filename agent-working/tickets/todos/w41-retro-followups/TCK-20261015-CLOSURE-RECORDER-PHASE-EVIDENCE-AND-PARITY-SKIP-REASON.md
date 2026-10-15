---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON
phase: open
date: 2026-10-15
tags: [agent-monitoring, data-quality, workflows]
---

# TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON

## Title
Hand-closure records which phases really ran from artifact evidence, needs a structured Parity skip reason when src/ changed, and the retro counts ledger blocks as gate failures

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, findings 2 and 5. 330 of 337 W41 + W42 runs were hand-closed, and 246 of 278 W41 runs carry the fixed
6-event template. The Paths section reports Investigate/Plan/Review/Architecture-Verify "omitted" on 125 W41 standard
closures, but 189 of 194 have full staging artifacts. The real gaps (9 standard tickets without artifacts) are buried.
Parity was skipped on 22 W41 and 4 W42 runs whose Files Changed lists `src/`, with only free-text reasons. The W42 Run
Summary says "Gate failures 0" while the Gates section shows 22 blocking Finalize verdicts, because the line counts run
final_status only.

## Scope
1. `record_hand_orchestrated_closure.py` derives the standard-tier phases that ran from evidence: staging/stored
   artifacts present means Investigate/Plan ran (recorded as such, with the artifact path in the summary). It only records
   omitted when the evidence is absent.
2. When the ticket's diff touches `src/` and Parity is skipped, a structured `skip_reason` from the enum is required (no
   free text alone). The recorder refuses otherwise, with a clear message, like its existing guards.
3. `generate_retro.py` Run Summary: show ledger blocking verdicts next to run gate failures (two labelled numbers), so
   "0" no longer hides blocks.

## Out of Scope
- Changing tiers or routing (the Paths routing candidates are the owner's next direction).
- Re-recording historical runs.

## Acceptance Criteria
- Tests: a standard ticket with stored artifacts records Investigate/Plan as ran; one without records them omitted; a
  src/ diff with Parity skipped and no enum reason is refused.
- W42's regenerated Run Summary shows 22 ledger blocks beside 0 run gate failures.

## Related Tickets
- TCK-20261006-EPIC-TICKET-PATH-RECORD
- TCK-20261009-HAND-CLOSURE-TEMPLATED-EVENTS-GUARD

## Related Docs
- docs/guides/agent_monitoring.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py, tools/agent-monitoring/generate_retro.py, tools/agent-monitoring/path_report.py

## Assumptions / Open Questions
- Assumption: the stored_artifacts path for a ticket is stable at closure time (staging moved before the recorder runs). Verify the order.

## Implementation Notes
(filled during work)

## Test Summary
(filled during work)

## Files Changed
(filled during work)

## Completion Summary
(filled at close)
