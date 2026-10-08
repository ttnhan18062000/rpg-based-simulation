---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261008-LAUNCHER-SQUASH-MERGED-BRANCH
phase: done
date: 2026-10-08
tags: [ai, process-improvement]
---

# TCK-20261008-LAUNCHER-SQUASH-MERGED-BRANCH

## Title
Launcher reuses a squash-merged recorded branch and ignores --branch

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`launch.py agent-working-planner --branch seat --dry-run` printed `git worktree add .../agent-working-planner agent-working-w40-close-and-card-fold`: it reused the recorded spent branch and ignored `--branch`. Fix C's `merge-base --is-ancestor` guard never fires because PRs are squash-merged. Dispatched by agent-working-planner.

## Scope
1. An explicit `--branch <topic>` always wins when the worktree is missing: bootstrap `<role>-<topic>` from origin/main whatever branch is recorded.
2. Without `--branch`, a recorded branch is spent if it is an ancestor of origin/main, has a merged PR (`gh pr list --head <b> --state merged`), or, when gh fails, `git cherry origin/main <b>` shows nothing unmerged. Then refuse and name `--branch`.
3. Folded in: an unresolvable push target (`$VAR`, substitution, glob) is treated like a possible push to the default branch (`push_default_branch`), and a double-quoted string holding a substitution is kept as an unknown value instead of an empty one.

## Out of Scope
Permission-mode launcher change (blocked on the owner).

## Acceptance Criteria
- [x] `--branch` overrides a live and a squash-merged recorded branch
- [x] squash-merged recorded branch refuses without `--branch` (gh mocked to fail -> cherry; gh merged PR)
- [x] `git push origin "$BRANCH"` and similar ask (push_default_branch)
- [x] `pytest tests/tools -k "session or guard or classify or roster"` green (826 passed)

## Related Tickets
TCK-20261007-SESSION-PER-ROLE-WORKTREES (#419), TCK-20261007-LAUNCHER-RELAUNCH-FIXES (fix C)

## Related Docs
docs/plans/agent_infrastructure/session_layer_working_process.md section 8

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
tools/sessions/launch.py, tools/sessions/classify.py, tests/tools/test_session_launch.py, tests/tools/test_session_classify.py

## Assumptions / Open Questions
A merged PR marks the branch spent even if it was later pushed to (the repo rule: a finished branch is never pushed to again).

## Implementation Notes
`branch_spent_reason()` in launch.py; `ensure_worktree` checks `topic and role` before any recorded-branch logic. classify.py: `_UNRESOLVABLE_REF` in `_push_destinations`; `_PLAIN_WORD` keeps single-token quoted operands (`"$BRANCH"`).

## Test Summary
826 passed, 1 skipped; 4 new launch tests, 2 new parametrized classify tests (9 cases).

## Files Changed
tools/sessions/launch.py, tools/sessions/classify.py, tests/tools/test_session_launch.py, tests/tools/test_session_classify.py, this ticket, monitoring shards.

## Completion Summary
A squash-merged recorded branch is now recognised as spent, and `--branch` always wins; a push to an unresolvable target asks.
