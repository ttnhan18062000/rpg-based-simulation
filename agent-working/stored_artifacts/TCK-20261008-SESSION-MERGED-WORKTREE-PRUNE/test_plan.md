---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE
artifact_type: test_plan
tags: [delivery, workflows]
---

# Test plan

`tests/tools/test_prune_merged_worktrees.py` (10 tests, fixture repo with real worktrees, gh mocked via `PrData`): each class (merged-clean removable; dirty; unmerged; open PR; seat; main) with its reason; dirty monitoring shard named by full path; tip moved after the merged PR; writer lease and live instance as seats; a real process with its cwd inside; gh unavailable gives one summary line; dry run changes nothing; `--execute` removes only removable, never passes `--force`, keeps the branch, writes the verified backup; a removal git refuses is reported, not forced; `--worktrees --remote` rejected. Regression: `test_session_prune_branches.py`, `test_prune_worktree_indexes.py`.
