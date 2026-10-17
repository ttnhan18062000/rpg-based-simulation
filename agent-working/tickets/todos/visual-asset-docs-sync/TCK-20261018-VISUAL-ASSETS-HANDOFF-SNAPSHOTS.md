---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS
phase: open
date: 2026-10-18
tags: [architecture, documentation]
---

# TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS

## Title
Refresh the tracked asset handover snapshots to the post-#608 state

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`docs/assets/session_handoff/{asset-planner,asset-implementer}.md` are tracked copies of the gitignored `.claude/handover/` notes. Sessions on another machine (u24desktop) pick up from them. Their last refresh predates #596 and #608, so a cross-machine pickup would start from stale state: it would miss rc-0011, the placeholder store guard, the #608 sandbox error and the entity-marker gates.

## Scope
- Rewrite both snapshots from the live notes: `.claude/handover/asset-planner.md` (asset-planner gives you its current text, or read it from the main checkout) and your own `.claude/handover/asset-implementer.md`. Same shape as today: a top quote line with the snapshot date and "the live handover is authoritative", then the note.
- Include this batch's result (ticket 1's owner decisions G4 and G6) and the gates: #523 and the role-id vs species+size choice.
- Remove anything a reader on another machine cannot act on: local-only paths that do not exist there, and live session names. Keep worktree paths only where they are labelled as this machine's.

## Out of Scope
- No change to the live `.claude/handover/` notes (gitignored, each seat's own).
- No other `docs/assets/` file.

## Acceptance Criteria
- [ ] Both snapshots are dated 2026-10-18 or later and match the live notes in substance (open items, gates, backlog, pending decisions).
- [ ] No secret, token or personal data; no `<...>` placeholder.
- [ ] Frontmatter valid (`python3 tools/validate_frontmatter.py` on both files and this ticket), and the scoped docs tests pass.

## Related Tickets
- Same batch: `TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT` (do it first)

## Related Docs
- `docs/assets/session_handoff/asset-planner.md`, `docs/assets/session_handoff/asset-implementer.md`

## Related Stored Artifacts
- None.

## Related Code Areas
- None (docs only).

## Assumptions / Open Questions
- Assumed: a snapshot is a copy, not a second source of truth. If the live note and the snapshot disagree later, the live note wins, as the snapshot's own header says.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
