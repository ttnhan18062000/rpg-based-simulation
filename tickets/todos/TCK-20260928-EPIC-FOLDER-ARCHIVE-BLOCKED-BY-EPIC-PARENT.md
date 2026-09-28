---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT
phase: open
date: 2026-09-28
tags: [process-improvement]
---

# TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT

## Title

Both folder-archive steps (implement-ticket.js Finalize step 3, implement-epic.js folder-cleanup)
require every `TCK-*.md` in a `tickets/todos/<folder>/` to be done, but the folder's own epic parent
never is, so neither step can archive an epic folder.

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P3

## Request Summary

Found while scoping `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`. The resurrection itself
was not caused by this, but the same folders expose it.

- `.claude/workflows/implement-ticket.js` Finalize step 3 (~line 1738, text at `origin/main`
  `9bcae32c5`) says: "If no TCK-*.md files remain (folder is empty or has only SEQUENCE.md /
  non-ticket files): mv <parent-dir>/ tickets/done/<FOLDER>/ … If other TCK-*.md files still exist
  in the folder: skip". An epic folder always still holds its epic-tier parent
  (`TCK-*-EPIC-*.md`, `## Status` `EPIC_SCOPED`), which no child close removes. The step therefore
  always skips for an epic folder.
- `.claude/workflows/implement-epic.js` folder-cleanup block (~line 409) says: "If any TCK-*.md
  file is NOT in tickets/done/ … print 'SKIPPED: unfinished tickets still in folder'". This is the
  same check with the same blocker: the epic parent is in the folder and not in `done/`. The
  `epic_id`-mode close step (`TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING`) closes an epic
  ticket, but only in `epic_id` mode. Folder mode's `epic_ticket_path` is always "".

The consequence is that every finished epic folder is archived by hand. Known cases:
`TCK-20260820-EPIC-WORLD-RENDERING-CORE` (manual close-out) and `mechanism-registry` (archived by
hand in #209 `8ab22a916`). Until someone notices, the epic-staleness hook nags a finished epic.

**Constraint any fix must respect:** moving a folder puts its epic parent under `tickets/done/`.
`check_ticket_location_consistency` (and its corpus test) then requires `status: historical`,
`phase: done` and a real close. So the epic parent must be **closed** (status, frontmatter,
working_log row, monitoring) before or as part of the move. It must never simply be moved while open.

## Scope

1. First, verify the implement-epic folder-mode claim above against `tests/tools/test_implement_epic_close_step.py`
   and the workflow text on the branch. If folder mode already handles the epic parent somewhere
   this ticket missed, record that and limit the fix to implement-ticket.js.
2. **implement-epic.js folder mode:** in the folder-cleanup check, exclude the folder's epic-tier
   parent from the "all TCK-*.md must be in done/" requirement. When every non-epic ticket is done,
   close that epic parent by reusing the existing `epic_id`-mode epic-close step's instructions
   (same helper or the same prompt block, not a second hand-written close), then move the folder.
3. **implement-ticket.js Finalize step 3:** when the only `TCK-*.md` left in the folder is the epic
   parent, do **not** close the epic from inside a child ticket's Finalize, which would be a
   different ticket's lifecycle. Print an explicit advisory instead:
   "All children of <folder> are done; epic parent <EPIC-ID> remains — close it via implement-epic
   (epic_id mode) or by hand." That turns today's silent skip into a visible next step.
4. Identify the epic parent structurally: `## Tier` `epic` (or `## Status` `EPIC_SCOPED`), read
   through `tools/ticket_field_values.py`'s parsing, not a filename match on `-EPIC-`.
5. **Retro cadence:** this changes workflow prompts. Regenerate the W39 retro before the prompt
   commit, as done for `TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS`.

## Out of Scope

- Closing `tickets/todos/progression-starvation-chain/`. That epic is genuinely open.
- Back-filling a close for any past epic that was archived by hand.

## Acceptance Criteria

- AC1: Given a synthetic folder with an `EPIC_SCOPED` parent, `SEQUENCE.md` and N children that
  are all in `done/`, implement-epic folder mode's cleanup closes the parent and moves the folder.
  Afterwards the location-consistency check passes for the moved parent.
- AC2: Given the same folder with one child not yet done, the cleanup still skips.
- AC3: implement-ticket Finalize step 3's text emits the advisory in the epic-parent-only case, and
  still moves a non-epic folder when no TCK files remain.
- AC4: The retro is regenerated before the prompt commit; bare `pytest tests/tools/` passes.

## Related Tickets

- `TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING`: the epic_id-mode close step to reuse.
- `TCK-20260820-EPIC-WORLD-RENDERING-CORE`: a prior manual close-out of this class.
- `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`: where this was found; a different cause.

## Related Docs

- `CLAUDE.md` "After Work" folder-move bullet. It states the rule ("when **all** tickets in the
  folder are done") and needs no change: the epic parent is closed as part of that.

## Related Stored Artifacts

None.

## Related Code Areas

- `.claude/workflows/implement-ticket.js` (Finalize step 3)
- `.claude/workflows/implement-epic.js` (folder-cleanup block, epic-close block)
- `tests/tools/test_implement_epic_close_step.py`
- `tools/ticket_field_values.py`

## Assumptions / Open Questions

- Assumes the epic-close step's instructions can be shared between the two implement-epic modes
  without behaviour change for `epic_id` mode. If they can't, stop and report rather than fork a
  second close path.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
