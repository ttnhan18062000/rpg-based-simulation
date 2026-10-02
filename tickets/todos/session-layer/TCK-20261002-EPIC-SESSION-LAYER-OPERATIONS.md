---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS
phase: open
date: 2026-10-02
tags: [ai, process-improvement, delivery]
---

# TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS

## Title
Epic C — Session-layer operations: a read-only view of what is in flight, and conservative worktree, branch and disk hygiene

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Worktrees and branches have no owner, no inventory and no retirement rule. On 2026-10-02 the volume reached
100% and blocked a `git push`: about 7.6 GB of worktrees, 307 local and 273 remote branches. It was cleaned by
hand (240 local and 161 remote branches deleted, with a name-to-SHA backup), using a heuristic ("every commit
subject already in `main`") that is **not** a safe deletion proof under squash merges.

This epic codifies that cleanup as tooling that is **read-only by default and conservative when it deletes**,
and gives the owner one command that answers "what is in flight?" It is operations work, justified by the
incident but **not part of the control-plane proof**, so it runs in parallel with Epics A and B and never
blocks them.

Binding plan: `docs/plans/agent_infrastructure/session_layer_working_process.md` (sections 8, 11, 6.1).

## Scope

- **`tools/sessions/status.py` (read-only).** Per seat: instance state (live / orphaned / none, from Epic A's
  role-state directory), worktree path, branch, dirty state, any git operation left in progress, open PR,
  size on disk, last commit and last activity. Also: seats held by a session that does not own them, and a
  session holding two seats.
- **Disk budget.** Warn at 85% of the volume and name the largest worktrees.
- **`tools/sessions/prune_branches.py` (dry-run by default).**
  - Stale means more than 7 days since the last commit; checked-out, open-PR and recent branches are skipped.
  - **Only a branch whose PR merged is eligible for deletion.** The commit-subject heuristic is shown as an
    informational hint and never as deletion safety. Branches with unique commits are listed with their owner
    and never auto-deleted.
  - A remote branch is eligible only if its PR merged **and** the remote tip still equals the merged PR's head.
  - A name-to-SHA backup is written first (restore: `git branch <name> <sha>` /
    `git push origin <sha>:refs/heads/<name>`), and remote deletions use `--force-with-lease` per branch.
  - Execution always needs the owner's approval; a remote delete is visible to everyone.
- **Worktree retirement report.** A worktree with no open PR and no unmerged unique commits, whose seat is
  retired or idle past a threshold, is reported as removable. Removal is the owner's call.

## Out of Scope

- Automatic deletion of anything, and any deletion the owner has not approved.
- Worktree creation and self-heal at launch (Epic A, M2).
- Routing, authority guardrails and message semantics (Epic B).
- Metrics and analytics beyond the status view (Epic D).
- Renaming the `doc-tag-enforcement` worktree to `agent-working` (pending; needs both sessions out of it).

## Acceptance Criteria

1. `status.py` reports the fields above for every worktree and seat, **read-only**: a test proves it changes no
   file, ref or worktree.
2. `prune_branches.py` runs dry-run by default and prints the classes (merged-PR, hint-only, unique-commits,
   skipped) with counts; a seeded repository proves that a **squash-merged branch with unique, unmerged
   commits is never classed deletable**.
3. The backup file is written before any deletion, restoring a deleted branch from it works, and a remote
   branch whose tip moved after the merge is skipped.
4. The disk warning fires at the threshold in a test with a faked volume reading and names the largest
   worktrees.
5. The retirement report lists a seeded removable worktree and does not list a worktree with an open PR or
   unique commits.
6. Reproducing the 2026-10-02 run in a copy of the data classes the same branches the same way, with the
   hint-only class reported separately.

## Related Tickets

- Needs Epic A's registry (M1) for seat ownership and its role-state directory (M2) for instance state:
  `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION`. May start after M1.
- Siblings: `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (B),
  `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW` (D).
- Parent of child tickets to be created by the agent-working planner.
- Precedent: the monitoring-shard checkout race and the worktree contract in `docs/guides/delivery_process.md`.

## Related Docs

- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding)
- `docs/guides/delivery_process.md` ("Worktree & Branch Isolation")
- `docs/guides/agent_session_reset_boundaries.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tools/sessions/status.py` and `prune_branches.py` (new); `git worktree`, `git for-each-ref` and `gh pr list`
(read); `registries/session_roles.yaml` (seat ownership); the role-state directory under the git common
directory.

## Assumptions / Open Questions

- `gh` can time out from this network; the tools degrade to "unknown PR state" and treat unknown as not
  deletable.
- Whether the threshold for "idle" worktrees is a fixed number of days or per-seat is a child-ticket decision.

## Implementation Notes

Child tickets are created later by the agent-working planner. Suggested, non-binding: `status.py`; disk
warning; `prune_branches.py` classification; backup and restore; remote-deletion guard; retirement report. The
tools **never delete on their own**: executing a deletion is a separate, owner-approved step.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
