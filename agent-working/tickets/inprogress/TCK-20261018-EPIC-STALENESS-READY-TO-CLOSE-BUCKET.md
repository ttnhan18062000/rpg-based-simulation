---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-EPIC-STALENESS-READY-TO-CLOSE-BUCKET
phase: open
date: 2026-10-18
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261018-EPIC-STALENESS-READY-TO-CLOSE-BUCKET

## Title
`epic_staleness_check` reports epics whose children are all done as "ready to close", not "stale"

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
The owner said yes on 2026-10-18 (via lead-planner, #634). In the triage of 8 "stale" epics, 4 were idle only because they were finished: every child was in `done/`. The report gave no way to tell "finished, close it" from "stuck".

## Scope
- In `tools/agent-monitoring/epic_staleness_check.py`, add a fourth bucket, **"Ready to close"**. A candidate goes there, instead of stale/never-started, when both hold:
  - (a) its folder holds no ticket file other than the epic itself (SEQUENCE.md and non-ticket files are ignored);
  - (b) every child ID it names resolves under `agent-working/tickets/done/`.
    - Child IDs are the `TCK-…` IDs in SEQUENCE.md and the epic body, excluding the epic's own ID and any ID whose ticket is epic-tier or a `FOLDER-` candidate. Cross-referenced epics aren't children.
    - At least one child is required.
    - An ID that resolves nowhere keeps the epic out of the bucket, and the line names that ID.
- A BLOCKED epic stays BLOCKED.
- The output section is "Ready to close (every child done; close the epic and move its folder to done/):". The JSON/structured output, if any, gains the same key.
- `make agent-monitoring-epic-staleness` and the PostToolUse nudge reuse the existing function; the nudge counts ready-to-close separately or not at all. Check what reads `compute_stale_epics_report` before changing its shape.
- Tests: all children done → ready; one child open → stale; a child ID missing everywhere → not ready, and named; a cross-referenced epic ID is ignored; BLOCKED wins; an empty child list → not ready.

## Out of Scope
- Auto-closing anything; the bucket is report-only.

## Acceptance Criteria
- Against a fixture that reproduces the 2026-10-18 triage shape (an epic plus SEQUENCE.md, all children done), the epic lands in Ready to close.
- The existing staleness tests stay green.

## Related Tickets
- TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC
- the 2026-10-18 epic closure commit (b18c28a29, #639)

## Related Docs
- docs/guides/agent_monitoring.md (staleness section)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/epic_staleness_check.py, its tests under tests/tools/ (or tests/unit/tools/)

## Assumptions / Open Questions
- none

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
