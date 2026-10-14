---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES
artifact_type: investigation
tags: [ai, process-improvement]
---

# investigation — TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES

- The one settings entry that runs `post_tool_hook.py` on every PostToolUse can host the check, so no settings.json change was needed.
- Measured: a call inside the throttle window costs about 36 microseconds in-process (state file read, no statvfs); the interpreter start of the hook dominates and is unchanged.
- The hand-run report on this host (43 worktrees) took about 40 s, almost all of it `measure()`'s tree walk plus two `gh pr list` calls. It listed 1 removable worktree (0.5 GB) and 6 detached clean ones (5.5 GB): d70-base 3.7 GB, walkbase 0.6 GB and four of 0.3 GB. Nothing was removed.
- `measure()` is called by the launcher when disk is low; it was left without the `gh` call so a launch never waits up to 2 minutes on the network.
- 14 run directories under `data/runs/` in this worktree (121 MB) were written on 2026-10-09 by pids 5169 and 1499, not by this session; they were reported, not deleted (delete_worktree_or_data is the user's).
