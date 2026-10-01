---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES

## Title
Port the 23 advisory and bookkeeping bash sites to args/runCommand and decide dispatch batching

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
Advisory (12) and bookkeeping (11) sites per classification.jsonl: `args` for start timestamp and execution id, `runCommand` otherwise, shadow-reviewer sites omitted. Includes the batching decision for 13 writeSidecar and 11 captureTs invocations (per-phase timestamps stamped by the existing monitoring agent, sidecar writes folded into the preceding agent) so the port does not add ~40 dispatches per run.

- Carried over from the parse-fix hotfix: take `start_ts` from `args` (today `scopeTs = await captureTs()` is a bash site pinned by tests), and decide the execution-id fallback: the clock-free `'fallback'` suffix means two runs of one ticket share an `execution_id` when the bash suffix fails and no `args.execution_id_suffix` is passed. Native path: return INVALID_ARGS when the arg is missing; legacy path: record the choice.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. The bookkeeping and advisory rows of classification.jsonl no longer call bash().
2. A recorded batching decision with measured or counted dispatches per full-tier run.
3. Monitoring run and event records for a legacy-path run are unchanged (pinned tests pass).

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
