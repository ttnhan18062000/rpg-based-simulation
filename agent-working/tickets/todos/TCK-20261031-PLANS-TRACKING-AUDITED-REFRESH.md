---
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20261031-PLANS-TRACKING-AUDITED-REFRESH
phase: open
date: 2026-10-31
tags: [planning, tracking, documentation]
---

# TCK-20261031-PLANS-TRACKING-AUDITED-REFRESH

## Title
Refresh docs/plans/plans_tracking.md with an audited count of the plans now on main

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`docs/plans/plans_tracking.md` is dated 2026-10-02 and omits the AI-first SDLC plan and everything since. The designer asked for a refresh under the owner's go on stale tickets and plans (#715 6543261623). It folds into the next agent-working PR after #796 merges, and is not a plan-only PR. Pushes and merges stay separate asks.

## Scope
Follow the file's own rules, working from the origin/main commit the branch is based on:
- Rebuild the inventory table against `docs/plans/`. Status and authority come from each plan's frontmatter. Do not infer completion from tickets.
- Exclude `docs/plans/archive/`. Collapse multi-file packages into one row, and exclude the file itself.
- Re-count files and records from the tree and record the totals in `## Scope`. Say this count is audited. Earlier counts were incremented, not audited: the file says 99 Markdown files, and `git ls-tree` at 6fdfdf555 finds 199 outside the archive including the file itself.
- Keep the brainstorm column to sources a plan explicitly references in `docs/brainstorm/`.
- Add any status value found in frontmatter to the status key, so that the key covers every value the table shows.
- Update the Date line.
- Check the paths named in the file's maintenance notes. Correct or remove a note only where its path has moved or been archived, and say so in the PR body. Do not re-judge a plan's accuracy or authority in those notes.

## Out of Scope
- Editing any plan or its frontmatter. If a plan's frontmatter is missing or looks wrong, the row shows what the file declares ("none" when it declares nothing), and the plan is listed in the PR body.
- Deciding who owns the file. `route` finds no owning domain, and the designer has raised that with lead-planner. This refresh does not settle it.
- Validating any plan's feasibility or implementation progress.
- A count check, test or other new tooling for this file.

## Acceptance Criteria
1. Every non-archive Markdown file under `docs/plans/`, except the file itself, is covered by exactly one table row. A scripted check from the tree shows this, and its output is in Test Summary.
2. The Scope totals match that check, with the commit it ran at, and are described as audited.
3. A sample of at least 10 rows, including every row for a multi-file package changed by this ticket, is checked against frontmatter by script or by reading: status and authority match.
4. Every relative link in the file resolves at that commit.
5. The Date line is updated. The AI-first SDLC plan has a row.
6. No file under `docs/plans/` other than `plans_tracking.md` changes.
7. Plans with missing or doubtful frontmatter are listed in the PR body, or the PR body says there are none.

## Related Tickets
TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
docs/plans/plans_tracking.md

## Related Stored Artifacts
None.

## Related Code Areas
None. No file under `tools/`, `tests/`, `docs/guides/` or `docs/guidelines/` names this file at 6fdfdf555.

## Assumptions / Open Questions
- Count at the base commit, not earlier. Other domains' plans can land before this ticket runs, so the 199 above is only a reference point.
- File ownership is open, as stated in Out of Scope.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
