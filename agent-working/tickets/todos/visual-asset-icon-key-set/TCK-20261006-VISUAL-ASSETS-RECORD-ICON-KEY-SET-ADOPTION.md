---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION
phase: open
date: 2026-10-06
tags: [architecture, testing, documentation]
---

# TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION

## Title
Record the user's adoption of icons-key-v1, re-point the guards, refresh the handoff snapshots and close the batch

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child 6 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`, **only if the user adopts `icons-key-v1`** (owner gate after child 5). Same pattern as
`TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION`.

## Scope
- Commit the user's adoption files byte for byte; re-point guards that describe the pre-adoption catalog by equality
  (`tests/visual_assets/adopted_facts.py`), never loosened.
- Docs state that no release candidate covers the new slots.
- Refresh `docs/assets/session_handoff/` snapshots; `SEQUENCE.md` status line.

## Out of Scope
- A release candidate. Panel wiring (next batch).

## Acceptance Criteria
- [ ] Adoption files committed unchanged; guards pinned to exact facts and passing.
- [ ] Handoff snapshots refreshed; batch status recorded.

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic), TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION (pattern)

## Related Docs
- docs/assets/session_handoff/

## Related Stored Artifacts


## Related Code Areas
- visual_assets/catalog/, tests/visual_assets/adopted_facts.py

## Assumptions / Open Questions
- If the user does not adopt, this ticket stays open and the PR carries children 1-5 only, by the user's choice.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

