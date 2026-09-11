---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-HOTFIX-LIVE-MAP-RECONNECTION-ROADMAP-STALE
phase: done
date: 2026-08-26
tags: [documentation, process-improvement]
---

# TCK-20260826-HOTFIX-LIVE-MAP-RECONNECTION-ROADMAP-STALE

## Title
`live_map_scaling_roadmap.md`'s M1 section and `live_map_reconnection_epic.md`'s frontmatter don't
reflect that the tracked epic already completed

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found live during `TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP`'s own investigation
(Scope item 1: check other roadmap docs for the same staleness class). `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`
is confirmed DONE (`tickets/done/live-map-reconnection/`, all 8 child tickets landed), but
`docs/plans/live_map_scaling_roadmap.md`'s M1 section header still just reads "M1 — Core
Reconnection (ships a real, working, connected map)" with no completion marker, and
`docs/plans/live_map_reconnection_epic.md`'s own frontmatter still says `status: active`.

## Scope
- Update `docs/plans/live_map_scaling_roadmap.md`'s M1 heading to mark it done, and add a brief
  completion note citing the epic's own real Completion Summary (8/8 child tickets, one honestly
  disclosed partial-criterion gap: live-browser FPS measurement couldn't run in the implementing
  sandbox).
- Update `docs/plans/live_map_reconnection_epic.md`'s frontmatter `status:` from `active` to
  `historical`, matching this repo's convention for a plan doc whose tracked epic has completed.

## Out of Scope
- Any change to the epic ticket itself or its child tickets — already correctly DONE.
- The `implement-epic.js` tracking_doc mechanism itself — that's the sibling ticket
  (`TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP`) which explicitly excludes `epic_id`
  mode from its own mechanism (this doc uses `epic_id` mode, not `folder` mode).

## Acceptance Criteria
- [x] `docs/plans/live_map_scaling_roadmap.md`'s M1 section accurately reflects the epic's real,
      current completion state.
- [x] `docs/plans/live_map_reconnection_epic.md`'s frontmatter `status:` reflects that its tracked
      epic is done.

## Related Tickets
- TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP (where this was found, during its own
  Scope item 1 investigation)
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION (the epic that completed)

## Related Docs
- docs/plans/live_map_scaling_roadmap.md
- docs/plans/live_map_reconnection_epic.md

## Related Stored Artifacts
None (hotfix — no staging artifacts).

## Related Code Areas
None (doc-only change).

## Assumptions / Open Questions
None — both facts (epic DONE, docs not updated) independently confirmed via direct file inspection.

## Implementation Notes
Doc-only fix. Cited the epic ticket's own real Completion Summary text (8/8 child tickets, the one
honestly-disclosed partial gap on live-browser FPS measurement) rather than writing a new,
independent completion claim.

## Test Summary
Doc-only change — no tests applicable. Verified by direct re-read of both files post-edit.

## Files Changed
- `docs/plans/live_map_scaling_roadmap.md`
- `docs/plans/live_map_reconnection_epic.md`

## Completion Summary
Fixed both confirmed staleness spots: the roadmap doc's M1 section now reflects the epic's real,
current DONE status (citing its own Completion Summary), and the epic's own detailed plan doc's
frontmatter status now reads `historical` instead of `active`.
