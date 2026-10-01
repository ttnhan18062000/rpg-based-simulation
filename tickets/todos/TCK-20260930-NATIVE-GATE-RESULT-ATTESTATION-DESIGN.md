---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN

## Title
Design and prototype verifiable gate results for agent-run commands in a native workflow

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The native runtime has no shell, so every gate in `implement-ticket.js` would be an agent running a command and reporting the result, which an agent can misreport. The classification found 7 gate rows and 2 control or input rows that need a result the script can verify rather than trust.

## Scope
- Design an attestation the script can check without trusting agent prose (candidate: a payload hash over an `args`-supplied nonce, computed by the tool; JS has no crypto so the check is a small inline function).
- Prototype on one gate (the Finalize self-check) in a throwaway script and try to forge it with an agent told to cheat.
- Record the residual risk and the dispatch cost; recommend adopt, adopt for gates only, or reject in favour of keeping implement-ticket on the legacy path.

## Out of Scope
- Porting implement-ticket.js.

## Acceptance Criteria
1. A written design with the attestation format and the checker.
2. A forgery attempt result (agent asked to report a pass without running) recorded.
3. A recommendation with cost per full-tier run.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION (the classification this follows from)
- TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT (sibling)
- TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT (pattern and measurement)

## Related Docs
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- Needs a real native run with agents; requires the user's explicit Workflow opt-in.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
