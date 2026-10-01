---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX

## Title
Make implement-ticket.js parse under the native Workflow runtime and remove its nondeterministic calls

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`implement-ticket.js` is rejected by the native `Workflow` tool (acorn error at line 182:78; a second raw-backtick site at line 1753) and uses `Date.now()` (line 261). Both block any native run and neither depends on the gate-routing decision.

## Scope
- Escape the raw backticks at lines 182 and 1753 (the only two parse blockers found).
- Take `start_ts` and `execution_id` from `args` instead of `date`/`Date.now()`; keep today's behavior when running through the legacy path.
- Pin parse status in `tests/tools/test_workflow_runtime_acorn_parse.py` (flip implement-ticket.js to ok).

## Out of Scope
- Any `bash()` change (the port ticket).

## Acceptance Criteria
1. implement-ticket.js parses with the runtime's acorn options.
2. No `Date.now(`, `Math.random(` or argless `new Date(` remains.
3. Existing implement-ticket tests pass unchanged.

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
- None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
