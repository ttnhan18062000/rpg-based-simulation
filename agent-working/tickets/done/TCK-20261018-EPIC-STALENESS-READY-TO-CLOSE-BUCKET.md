---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-EPIC-STALENESS-READY-TO-CLOSE-BUCKET
phase: done
date: 2026-10-18
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261018-EPIC-STALENESS-READY-TO-CLOSE-BUCKET

## Title
`epic_staleness_check` reports epics whose children are all done as "ready to close", not "stale"

## Status
DONE

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
- `_classify_candidates` (private; only `find_stale_epics` and `compute_stale_epics_report` consume it, plus tests through those) now returns `(stale, never_started, blocked, ready, unresolved)`. `find_stale_epics` takes index 0 only, so the hook nudge never counts a ready epic.
- `_ready_to_close_verdict` uses one `rglob("TCK-*.md")` index of the tickets root (`inprogress_dir.parent`): the epic's own ID and other candidates' epic IDs are excluded, epic-tier tickets are cross-references, an ID found only outside `done/` is an open child, an ID found nowhere is unresolved. BLOCKED is decided first. Folder mode also requires that no ticket file other than the epic is left in the folder; epic_id mode (an epic in `inprogress/`) has no folder, so only the children rule applies.
- The "unresolved" section is shown only when at least one child resolves and every resolvable child is done, so a not-yet-filed plan does not add noise (an earlier version listed those and broke two existing exact-count tests).
- Real-data check: `make agent-monitoring-epic-staleness` on this branch (origin/main plus the planner's batch commits, the four epics already closed) lists nothing under Ready to close and no unresolved section.

## Test Summary
`tests/tools/test_epic_staleness_check.py`, `test_monitoring_hook_subdirectory_cwd.py`, `test_status_drift_check.py`: 65 passed (8 new): all children done → ready and not stale or hook-visible; one open child → stale; a ghost ID blocks and is named; cross-referenced epics (done and in-progress) ignored; BLOCKED wins; no children → not ready; a stray sibling ticket blocks; the hook never counts a ready epic.

## Files Changed
- tools/agent-monitoring/epic_staleness_check.py
- tests/tools/test_epic_staleness_check.py
- docs/guides/agent_monitoring.md

## Completion Summary
`epic_staleness_check` reports a finished epic (no ticket left in its folder, every named child in done/) under "Ready to close" instead of as stale; unresolved child IDs are named; BLOCKED still wins; the hook nudge is unchanged.
