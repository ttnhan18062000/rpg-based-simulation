---
status: active
layer: ticket
authority: P2
audience: agent
ticket_id: TCK-20260916-DOC-COVERAGE-CHECK-BLIND-TO-COMMITTED-CHANGES
phase: open
date: 2026-09-16
tags: [ticket-scoper, process-improvement]
---

# TCK-20260916-DOC-COVERAGE-CHECK-BLIND-TO-COMMITTED-CHANGES

## Title
`check_docs_to_update_coverage`'s reverse-direction check only reads uncommitted `git status`, producing a false FAIL for a hand-orchestrated ticket that commits its doc edits incrementally instead of leaving them uncommitted until Finalize

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary

`tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`'s reverse-direction half
(`_git_touched_paths()`) calls `git status --porcelain` only — this reflects uncommitted
working-tree changes, not the ticket's full diff against the base branch. A ticket worked
hand-orchestrated (not via the formal `implement-ticket.js` pipeline) that commits incrementally
as it progresses — an established, encouraged practice in this repo (see e.g. the "chain commit +
checkout in one Bash invocation" guidance in CLAUDE.md's Worktree & Branch Isolation section, and
the general discipline of committing real work promptly rather than leaving it uncommitted for
long stretches) — will have a clean working tree by the time Finalize/done-checker runs, even
though the docs genuinely were updated and genuinely are part of the branch's diff.

Found live during `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`'s own hand-orchestrated closure:
`docs/brainstorm/rpg_feature_atlas.html` and `docs/brainstorm/rpg_simulation_wiring_map.html` were
both genuinely edited, both cited correctly in that ticket's own `investigation.md` "Docs Requiring
Update" section, and both committed several commits earlier on the same branch (confirmed via
`git diff origin/main --stat -- <paths>`, which shows real changes) — but
`check_docs_to_update_coverage` reported `FAIL` because `git status --porcelain` was clean at
check time.

## Scope

- Change `_git_touched_paths()` (or add a second helper used by this one check) to also include
  paths touched by the current branch's full diff against its base — e.g.
  `git diff <merge-base>...HEAD --name-only`, unioned with the existing `git status --porcelain`
  output — so a ticket's committed-but-not-yet-uncommitted doc edits are still recognized.
- Determine the right base-branch reference to diff against (likely `origin/main`, matching the
  convention already used elsewhere in this file's own module, e.g. the base-branch collect-only
  pattern in `.github/workflows/test.yml`) — confirm rather than assume, since a wrong base could
  either over- or under-report touched paths.

## Out of Scope

- Any other done-checker condition.
- Changing the forward-direction half of `check_docs_to_update_coverage` (unaffected by this gap).

## Acceptance Criteria

- [ ] A ticket that edits and commits a `docs/` path mid-session (not left uncommitted until
      Finalize) no longer produces a false `FAIL` from `check_docs_to_update_coverage`'s reverse
      direction, when that path is correctly cited in the ticket's own body/investigation text.
- [ ] The forward-direction half's existing behavior is unchanged (still flags a docs path named
      in `investigation.md` but never touched at all, committed or not).
- [ ] A real test using a fixture that commits a doc change mid-"session" (not just leaves it
      uncommitted) proves the fix, not just a clean pass on the existing uncommitted-change case.

## Related Tickets
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — where this was found live, closed by working
  around it with documented justification (real `git diff origin/main` verification) rather than
  blocked on this fix.
- `TCK-20260802-DOC-COVERAGE-CHECK` — original forward-direction check this reverse half was added
  alongside.
- `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK` — introduced the reverse-direction half this ticket
  reports a gap in.

## Related Docs
- None yet.

## Related Stored Artifacts
- None — hotfix tier, self-evident intent per this ticket's own body.

## Related Code Areas
- `tools/gate_checks/done_checker_static.py::_git_touched_paths`
- `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`

## Assumptions / Open Questions
- Whether `origin/main` is always the right base, or whether it should resolve the actual base
  branch dynamically (relevant if this repo's default branch name ever changes, or for a ticket
  stacked on a non-`main` branch).

## Implementation Notes
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed as a real, small, well-understood gap rather than silently routed around — the
underlying substance (docs genuinely updated and cited) was independently verified via
`git diff origin/main --stat` before closing the ticket that surfaced this.
