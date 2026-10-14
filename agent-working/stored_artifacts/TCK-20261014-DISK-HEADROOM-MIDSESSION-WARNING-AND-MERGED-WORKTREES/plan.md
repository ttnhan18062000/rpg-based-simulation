---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES
artifact_type: plan
tags: [ai, process-improvement]
---

# plan — TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES

1. `tools/sessions/disk_warning.py::mid_session_line`: a per-session state file under `.claude/` (gitignored) holds the last check and last warning times; inside the 10-minute window it returns with no statvfs; outside it one statvfs, a line below the threshold at most every 30 minutes and at once on the first drop below 2 GB.
2. `tools/agent-monitoring/post_tool_hook.py` calls it after writing its record, inside its own try/except, and prints a PostToolUse `additionalContext`. The existing settings.json entry hosts it; settings.json is not touched.
3. `disk_headroom.py`: `removable_worktrees()` reuses `prune_branches.classify_worktrees` (new constant `DETACHED_REASON` instead of a repeated string) and is shown by the hand-run report and `--json`. `measure()` and the launcher are unchanged so launch never waits on `gh`.
4. Docs: the disk-headroom section of `docs/guides/agent_session_reset_boundaries.md`.
