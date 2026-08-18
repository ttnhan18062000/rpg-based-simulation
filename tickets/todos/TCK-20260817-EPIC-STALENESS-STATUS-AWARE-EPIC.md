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
OPEN

## Tier
hotfix

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
Full findings are in `docs/plans/epic_staleness_status_aware_epic.md`. Concrete scope:
- Teach the staleness-check script (`tools/agent-monitoring/`) to read the target ticket's
  `## Status` body field before flagging, and skip (or flag with a different, non-actionable
  label) any ticket whose status is `BLOCKED` with a stated rationale.
- Decide whether `BLOCKED` tickets should still surface in the report as an informational
  "parked" list, rather than disappear entirely.

## Out of Scope
- Any change to the 5-day staleness threshold itself.
- Broader agent-monitoring tooling changes beyond this one hook's status-awareness.

## Acceptance Criteria
- [ ] Running the staleness check against `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` in its
      current `BLOCKED` state no longer produces the same undifferentiated "stale" flag it does today.
- [ ] A genuinely stale, non-`BLOCKED` epic still gets flagged correctly (the fix must not weaken
      the hook's real usefulness).

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
  disappear entirely, is an open decision to resolve during implementation.
- **Downgraded from epic to hotfix tier (2026-08-18):** the most clear-cut miscall of the 10
  sub-epics created under `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC` — this ticket's own
  Request Summary already described the fix as "small, precisely scoped," which was never
  epic-shaped to begin with. Hotfix tier needs no staging artifacts, per Tier Routing.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
