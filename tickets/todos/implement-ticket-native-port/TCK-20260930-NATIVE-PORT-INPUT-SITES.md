---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-INPUT-SITES
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-INPUT-SITES

## Title
Port the 5 input-class bash sites to runCommand

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES.

## Scope
Input sites compute values handed to agents or gates; failure is visible to the receiving agent so plain `runCommand` is enough, except the parity-ledger `git status` that feeds a gate, which waits for the attested route.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. The input rows (except the parity-ledger status) no longer call bash().
2. Markers parsed as `{exit_code, stdout}` as in the create-tickets pilot.
3. Existing pinned tests pass or are updated with the same assertions.

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
