---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES

## Title
Port the 9 gate and control bash sites using the attested route

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP, TCK-20260930-NATIVE-PORT-INPUT-SITES.

## Scope
Promote the prototype (`stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/prototype/`) to `tools/` with tests, inline the SHA-256 verifier in implement-ticket.js, and route the gate (7) and control (3, where a wrong answer skips required work) sites through it. State in code comments and docs that it is anti-misreport, not tamper-proof.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. No gate-class site calls bash().
2. Checker unit tests: honest pass, honest fail, wrong command, wrong gate, tampered exit_code, wrong nonce.
3. The backstop child is landed first so enforcement does not rest on attestation.

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
