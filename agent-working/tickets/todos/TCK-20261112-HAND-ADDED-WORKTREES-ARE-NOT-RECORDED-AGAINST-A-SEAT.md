---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT
phase: open
date: 2026-11-12
tags: [planning, delivery]
---

# TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT

## Title
A worktree a seat creates with a plain `git worktree add` is never recorded against that seat, so status.py and project_sync can't name who works in it

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while P1a (TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE) was being planned. The P0 dry run labels almost every rpg row
`rpg (unmapped)`. agent-working-designer-u24 rejected a guessed seat map, so P1a labels these `<domain> (seat not recorded)`.
lead-planner-u24 (2026-11-12): file it at P3, **parked, not dispatched**. It rides the next agent-working PR as a filing. Revisit
after P1b, once the board shows how many rows it affects.

## Scope
Lead's scope note:
- `launch.py --worktree` already records a batch worktree; status.py reads it as `writing_in`.
- The gap is seats that run `git worktree add` by hand, for example nonflight, recruit, rpg and
  /mnt/data/scratch-rpg-implementer/*.
- The cheapest fix may be a `tools/sessions` "add worktree" command that creates the worktree and records it with the same
  record `--worktree` writes, plus one line in the session-role guidance saying to use it. That would be better than a new
  record type.
1. Count the affected rows on the live board (after P1b) before choosing.
2. If the command is chosen: the command, the role-guidance line, and about 3 tests (records it, refuses an existing path,
   status.py reads it as `writing_in`).

## Out of Scope
- Guessing seats from branch names or a static map (the designer rejected this in the P1a plan review).
- Back-filling records for worktrees that already exist.

## Acceptance Criteria
1. A worktree created through the new path shows its seat in `status.py` and in `project_sync.py --dry-run`.
2. The role guidance names the command. Scoped tests only.

## Related Tickets
- TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE (P1a, where it was found)
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW
- Received 2026-11-14 from TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW (closed, owner #715 6875225978): the M6b roster-check item "worktrees with no role" is this ticket.

## Related Docs
- docs/guidelines/session_roles/

## Related Stored Artifacts
- none

## Related Code Areas
- tools/sessions/launch.py (`--worktree`), tools/sessions/status.py (`writing_in`, `_worktree_for`)

## Assumptions / Open Questions
- Simpler-fix check (6698958617): reusing the record `--worktree` already writes is cheaper than a new record. The cost is
  about 40 lines and 3 tests, plus a guidance line. Worktrees created by hand outside the command stay unrecorded.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
