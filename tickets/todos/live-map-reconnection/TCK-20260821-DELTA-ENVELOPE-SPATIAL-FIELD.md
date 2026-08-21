---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD
phase: open
date: 2026-08-21
tags: []
---

# TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD

## Title
Reserve a spatial-subscription placeholder field in the WS delta envelope

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Bandwidth analysis at real target scale (10,000 entities) shows interest management (filtering what's broadcast by what a viewer can see) is likely necessary, not safely deferrable as originally assumed. The author wants an unused region/chunk field reserved now in the delta message envelope so a future interest-management feature doesn't require a breaking protocol change later -- building the actual filtering logic stays out of scope for this epic.

## Scope
- Add one additional key (e.g. region or chunk) to the delta envelope produced by the entity-delta broadcast path, present but null/unset on every message
- Land in the same PR/session as the delta broadcast ticket or immediately after, since it has no implementation surface of its own until that envelope exists

## Out of Scope
- Any server-side filtering logic that reads or acts on the new field's value (belongs solely to the separate M3 interest-management epic, TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT)
- Stubbing subscription semantics, per-viewer filtering hooks, or client-side sending of the field
- Any protocol_version bump (must be additive-only)

## Acceptance Criteria
- [ ] the delta envelope from the entity-delta broadcast path includes an additional key (e.g. region or chunk) present but null/unset on every message
- [ ] adding the field does not change any existing field's name/type/semantics, no protocol_version bump needed
- [ ] no server-side filtering logic reads or acts on the new field's value anywhere in this ticket's diff (grep for the field name outside envelope construction/schema definition returns nothing)
- [ ] tests for the delta envelope continue to pass unmodified except for the new field's presence

## Related Tickets
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/ws/stream.py
- src/api/presenters/state_presenter.py

## Assumptions / Open Questions
- field name/type not yet decided (region vs chunk, string ID vs coordinate vs bounding box) -- only needs a placeholder reasonably compatible with whatever the downstream interest-management epic later chooses, not final granularity design
- layer corrected to `engine` post-write (initially set to `observability` by the write agent, self-flagged as a stretch — `engine` matches the sibling `TCK-20260821-WS-ENTITY-DELTA-BROADCAST` ticket it hard-depends on and the actual file both touch, `src/api/ws/stream.py`)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
