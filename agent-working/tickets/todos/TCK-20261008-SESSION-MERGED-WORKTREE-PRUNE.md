---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE
phase: open
date: 2026-10-08
tags: [delivery, workflows]
---

# TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE

## Title
Classify worktrees whose branch is merged, and let the owner remove them in one guarded call

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The 2026-10-08 disk incident was resolved by a one-off scratchpad script. For each worktree, it checked: clean except monitoring shards, branch tip equal to a MERGED PR head, no process with its cwd inside. It then ran `git worktree remove` (no --force) on the survivors, removing 24 worktrees and freeing about 12 GB. Six were refused because they held uncommitted files that the "ignore monitoring shards" filter had hidden. `tools/sessions/prune_branches.py` already does this classification for branches, but skips any branch that is checked out in a worktree, which is exactly the merged-worktree case.

## Scope
- Extend `prune_branches.py` (or add a sibling) with a worktree mode: dry run by default, listing each worktree as removable (merged PR, tip equals head, clean, not a live session's home worktree per the session state, no process cwd inside) or kept, with a reason.
- Dirtiness is reported in full. A dirty monitoring shard is shown as a reason (with the file names), never silently ignored.
- `--execute` runs `git worktree remove` without --force on removable entries only, and prints the freed size. It keeps branches and writes the same name-to-SHA backup the branch mode writes.
- Never touches session seat worktrees or worktrees with an open PR.

## Out of Scope
Deleting branches (already covered by branch mode). Deleting `data/runs` content. Running automatically. This stays an owner-run command (delete_worktree_or_data).

## Acceptance Criteria
1. On a fixture repo, it classifies merged-clean, merged-dirty, unmerged, open-PR and seat worktrees correctly (with gh mocked).
2. A dry run changes nothing; `--execute` removes only removable entries and never passes --force.
3. A worktree with only a dirty monitoring shard is listed as kept, with the shard named.
4. Scoped tests under tests/tools pass.

## Related Tickets
TCK-20261008-SESSION-DISK-HEADROOM-GUARD

## Related Docs
docs/guides/delivery_process.md (Worktree & Branch Isolation)

## Related Stored Artifacts
agent-working/agent-monitoring/retro/RETRO-2026-W41.md (Addendum 2026-10-08)

## Related Code Areas
tools/sessions/prune_branches.py, tools/sessions/state.py

## Assumptions / Open Questions
None.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
