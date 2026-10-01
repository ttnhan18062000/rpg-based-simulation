---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP

## Title
Re-run the static gates orchestrator-side after a native run returns

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: none in this batch.

## Scope
The attestation design found agent-reported gate results forgeable. Add the unforgeable backstop: after a native implement-ticket run returns, the top-level session (which has a shell) re-runs `done_checker_static.py` and the validators before commit; document it in the implement-ticket skill and `docs/guides/delivery_process.md`. CI remains the second backstop.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. A documented, runnable post-native-run check (one command) that exits non-zero on any gate failure.
2. The implement-ticket skill instructs running it before commit.
3. Test that the check fails on a ticket with a missing working_log row.

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
