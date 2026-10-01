---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT

## Title
Port implement-ticket.js to the native Workflow runtime in the classified order

## Status
EPIC_SCOPED

## Tier
epic

## Type
refactor

## Priority
P2

## Request Summary
Follows the classification: advisory and bookkeeping sites first, then input sites, then gates with attestation, plus the dispatch-cost batching decision (13 writeSidecar and 11 captureTs invocations).

## Scope
- Children: advisory and bookkeeping sites via `runCommand`/`args`; input sites; gate and control sites using the attested route from the design ticket; per-phase timestamp and sidecar batching.
- Blocked by `TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX` and `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN`.

## Out of Scope
- Any other workflow script.

## Acceptance Criteria
1. No `bash(` remains in implement-ticket.js.
2. Every gate-class site uses the attested route or stays orchestrator-side by an explicit, recorded decision.
3. One native run of a small ticket completes with correct gate outcomes.

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
- Attestation design outcome (`stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`): **adopt for gates only**. A nonce-hash attestation was forged on the first try by a cheat-instructed agent, so it is anti-misreport only; the unforgeable check is an orchestrator-side re-run of the static gates plus CI. AC2 is therefore met by "attested route + recorded orchestrator backstop", not by attestation alone.
- **Deliberate partial run (user decision, 2026-10-01):** only 3 of the 5 children run now (BOOKKEEPING-ADVISORY-SITES, INPUT-SITES, ORCHESTRATOR-BACKSTOP; all done and moved to `tickets/done/`). `TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES` and `TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN` are deferred and stay in this folder. Reason: the design measured about 450k tokens and about 3 minutes extra per run if all 9 gate sites are reached, so the user decides on the gate children after seeing the cheap children's measured cost. This is a recorded exception, not a breach of the epic all-or-nothing rule. The epic stays OPEN and is not moved to done.
- Children are in this folder; order in `SEQUENCE.md`. No child started in the scoping batch.

## Implementation Notes
Scoped 2026-10-01 into 5 children (see `SEQUENCE.md`). Epic closes when all children are done; 3 of 5 are done, 2 deferred by user decision (see Assumptions).

## Test Summary

## Files Changed

## Completion Summary
