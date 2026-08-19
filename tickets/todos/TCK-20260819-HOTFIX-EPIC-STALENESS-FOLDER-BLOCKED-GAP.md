---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP
phase: open
date: 2026-08-19
tags: [ai, agent-monitoring]
---

# TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP

## Title
epic_staleness_check.py's folder-granularity candidates never see BLOCKED status, unlike ticket-granularity ones

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` (done, 2026-08-19) taught
`epic_staleness_check.py` to read a candidate epic's `## Status` body field and skip flagging it
stale when `BLOCKED`. That fix only reaches `discover_candidate_epics()`'s `inprogress_dir` branch
(ticket-file candidates). The sibling `todos_dir` branch (folder-level candidates, `mode="folder"`,
`epic_id` prefixed `FOLDER-`) only sets `status` by looking for an epic-tier `TCK-*.md` file
**inside that same subfolder** (`epic_staleness_check.py:174-182`); when no such file exists there
— which is the case for `codex-runtime-activation`, whose real governing epic ticket
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md` lives in `tickets/inprogress/`, a different
directory — `status` falls through to `None` (`epic_staleness_check.py:194`), so the folder
candidate can never be classified `BLOCKED` and always falls back to plain staleness-by-idle-time.
Live-confirmed: `make agent-monitoring-epic-staleness` currently reports the ticket
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` correctly in the "Informational: BLOCKED epics"
bucket, while `FOLDER-tickets-todos-codex-runtime-activation` — the same underlying epic, folder
granularity — still reports in the genuinely-"Stale epics" bucket. This is the exact false-positive
class `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` was built to eliminate, recurring one layer
down because the fix landed on one of two independent status-derivation code paths, not both.

## Scope
- In `discover_candidate_epics()`'s `todos_dir` branch (`epic_staleness_check.py`), when no
  epic-tier ticket file is found inside the subfolder itself, cross-reference `tickets/inprogress/`
  (and/or the folder's child ticket IDs' own `## Related Tickets`/parent-epic references) to find
  the governing epic ticket and read its `## Status` from there, instead of leaving `status=None`.
- Add a regression test using the real `codex-runtime-activation` case (or an equivalent fixture)
  proving `FOLDER-tickets-todos-codex-runtime-activation` now lands in the BLOCKED bucket, not the
  stale bucket, matching `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`'s own classification.

## Out of Scope
- Any change to the `inprogress_dir` branch, which already works correctly.
- Broader review of every other checker in `tools/agent-monitoring/`/`tools/gate_checks/` for the
  same "fix landed on one code path, not its sibling" pattern — a live investigation this session
  already spot-checked `epic_scope_orphan_check.py` (clean, no duality) and
  `status_drift_check.py` (different, unrelated gap — see
  `TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP`); a fuller sweep is a separate, larger effort
  not scoped here.

## Acceptance Criteria
- [ ] `make agent-monitoring-epic-staleness` classifies `FOLDER-tickets-todos-codex-runtime-
      activation` in the "Informational: BLOCKED epics" bucket, consistent with its governing
      ticket's own classification — not in "Stale epics".
- [ ] A genuinely stale (non-blocked) folder-mode candidate still correctly flags as stale — the
      fix must not weaken real detection, same bar `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-
      EPIC` held itself to.
- [ ] New regression test added and passing.

## Related Tickets
- TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC (the original fix this ticket extends to the
  folder-granularity code path it didn't reach)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (the concrete live case proving the gap)
- TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP (sibling finding from the same session
  investigation into this tooling tree's checker-consistency gaps, unrelated root cause)

## Related Docs
- docs/guides/agent_monitoring.md

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- tools/agent-monitoring/epic_staleness_check.py (`discover_candidate_epics`, lines ~167-216)
- tests/tools/test_epic_staleness_check.py (if it exists) or equivalent

## Assumptions / Open Questions
- Exact cross-referencing mechanism (scan `tickets/inprogress/` for a ticket whose child-IDs list
  includes this folder's tickets, vs. a simpler folder-name-to-epic-id convention lookup) is left
  to the implementer — whichever is more robust against future folder/epic-ticket naming drift.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
