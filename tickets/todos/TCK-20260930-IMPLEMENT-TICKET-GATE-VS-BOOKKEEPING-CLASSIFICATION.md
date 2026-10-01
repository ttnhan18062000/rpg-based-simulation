---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION
phase: open
date: 2026-09-30
tags: [ai, agent-monitoring]
---

# TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION

## Title
Classify every `bash()` site in `implement-ticket.js` as gate or bookkeeping before any native port

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The `create-tickets` pilot found that routing shell through `runCommand()` (an agent) weakens the
orchestrator-side guarantee that an agent never reports "gate passed". `implement-ticket.js` has
about 50 `bash()` sites, most of them gate checks, so a mechanical port is unsafe. Produce the
per-site classification and a decision on each class. This ticket is the decision only; it ports
nothing.

## Scope
1. Enumerate every `bash()` site (`grep -c` shows 50 at the time of filing) with line, purpose,
   and the decision it feeds (blocking verdict, advisory WARN, timestamp, sidecar/monitoring write,
   git/status read).
2. Classify each as **gate** (result decides pass/fail), **advisory** (never blocks), or
   **bookkeeping** (no verdict).
3. For each class, decide the native-port route: stays orchestrator-side, goes through
   `runCommand()` with script-parsed `{exit_code, stdout}` markers, or becomes an `args`-supplied
   value. Record the residual misreport risk for any gate routed through an agent.
4. Measure, don't assume, whether the native runtime offers any non-agent shell path usable for
   gates. Cite the pilot measurement.
5. Output: a classification table in a stored artifact, plus a recommended port sequence as
   follow-up tickets (filed, not folded in).

## Out of Scope
- Porting `implement-ticket.js` or editing it.
- `implement-epic.js` (`TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT`).

## Acceptance Criteria
1. The table covers every `bash(` site; a test or script check confirms the count matches the file.
2. Every row has a class and a route, and every gate-class row states its misreport risk.
3. The non-agent shell path question is answered with evidence.
4. Follow-up port tickets are filed for each route that needs code.

## Related Tickets
- TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT (done; the finding behind this)
- TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT (sibling)
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (backlog parent)

## Related Docs
- `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/pilot_measurement.md`
- `docs/ai/skills.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `tools/gate_checks/`

## Assumptions / Open Questions
- Open: is there any non-agent shell path in the native runtime? The pilot suggests not.

## Implementation Notes
Draft by agent-working-design; the implementer commits it.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
