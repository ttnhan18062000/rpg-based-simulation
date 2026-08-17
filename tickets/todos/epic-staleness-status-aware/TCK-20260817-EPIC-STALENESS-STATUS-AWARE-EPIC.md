---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC
phase: open
date: 2026-08-17
tags: [ai, process-improvement]
---

# TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC

## Title
Teach the epic-staleness hook to check ticket ## Status before flagging BLOCKED epics as stale

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P1

## Request Summary
`make agent-monitoring-epic-staleness` measures file-mtime idleness only. It has flagged
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` as idle throughout this entire session, despite that
ticket's frontmatter literally stating `phase: blocked` and its body carrying a dated, explicit
deferral rationale. This is a deliberately governed pause, fully documented — not ambiguous
ownership or silent neglect — and it has fired repeatedly in this session's own tool output while
this exact ticket was being written. Small, precisely scoped, high-value fix: teach the hook to
read ticket status before flagging.

## Scope
- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/epic_staleness_status_aware_epic.md`. Detailed, investigated child tickets are not
  created yet.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's item
  (status-aware staleness check, decide whether BLOCKED epics still surface informationally),
  producing investigated child tickets in `tickets/todos/epic-staleness-status-aware/`.

## Out of Scope
- Any change to the 5-day staleness threshold itself.
- Broader agent-monitoring tooling changes beyond this one hook's status-awareness.

## Acceptance Criteria
- [ ] `docs/plans/epic_staleness_status_aware_epic.md` is reviewed and its scope confirmed accurate.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (the concrete false-positive case study)

## Related Docs
- docs/plans/epic_staleness_status_aware_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/ (the epic-staleness check script)

## Assumptions / Open Questions
- Whether BLOCKED epics should still appear in the report as an informational "parked" list, or
  disappear entirely, is an open decision for whoever scopes the child ticket.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
