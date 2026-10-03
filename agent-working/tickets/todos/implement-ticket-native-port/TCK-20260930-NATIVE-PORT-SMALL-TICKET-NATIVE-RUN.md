---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN

## Title
Run one small ticket through the native implement-ticket and verify gate outcomes

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES.

## Scope
Epic AC1 and AC3: no `bash(` in implement-ticket.js and one native run of a small ticket with correct gate outcomes (including a deliberately failing gate). Requires the user's own Workflow opt-in at dispatch time.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. `tools/workflow_bash_sites.py` reports 0 real sites.
2. One native run completes with correct pass and fail outcomes, recorded as evidence in `.jsonl`/`.md`.
3. The orchestrator backstop agrees with the run's gate verdicts.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (parent epic)
- TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN (outcome: adopt for gates only, plus backstop)

## Related Docs
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.md`
- `stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/`
- `stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- None beyond the parent epic's.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
