---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES
phase: open
date: 2026-10-14
tags: [ai, process-improvement]
---

# TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES

## Title
Warn about low disk space mid-session, not only at SessionStart, and list worktrees whose branch is merged in the disk report

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
On 2026-10-14 `/mnt/data` reached 0 bytes free. The day before it had 22.9 GB free. This is the third time, after
2026-10-08 and 2026-10-11. The headroom warning from TCK-20261008-SESSION-DISK-HEADROOM-GUARD fires only at
SessionStart and at launch, and long-running sessions never start again during a working day. lead-planner-u24
suggested two report-only additions, and the owner chose both in the agent-working-planner terminal (2026-10-14).
Most of the space was held by worktrees whose branch had already merged.

## Scope
1. **Mid-session warning.** In the existing PostToolUse hook path (`tools/agent-monitoring/post_tool_hook.py`, or a
   small sibling called from the same settings entry; prefer no new settings.json entry), call
   `disk_headroom.free_bytes()` (one `statvfs`):
   - throttled to at most once per 10 minutes per session, using a timestamp file under the session's gitignored
     state dir;
   - when free space is below the threshold (`SESSION_DISK_THRESHOLD_GB`, default 10), emit one `additionalContext`
     line naming the free GB and the two commands below;
   - repeat the line at most once per 30 minutes while it stays low, and at once if it drops below 2 GB.
   It must never fail or slow a tool call: wrap everything, and spend no more than one statvfs per throttle window.
2. **Merged-worktree listing in the disk report.** When `disk_headroom.measure()` runs (below the threshold, or by
   hand), add a "Removable worktrees" section. It lists worktrees whose branch tip equals a merged PR head, with size,
   reusing `tools/sessions/prune_branches.py`'s existing worktree classification (`--worktrees`). Never re-implement
   it. Also show worktrees with a detached HEAD and no uncommitted changes as "detached, check". Report only. The
   line points at `python3 -m tools.sessions.prune_branches --worktrees --execute --backup <path>`, which still needs
   the user's yes (delete_worktree_or_data).
   If `gh` is unavailable, the section says so and lists nothing as removable.
3. Docs: update the disk-headroom section of the session-layer guide (or wherever the TCK-20261008 behaviour is
   documented) with the mid-session warning and the new section.
4. Tests in `tests/tools/`:
   - throttle: no second statvfs inside the window;
   - a warning below the threshold and none above it;
   - the < 2 GB escalation;
   - the hook swallows an exception from statvfs;
   - the report lists a merged-head worktree, does not list a unique-commits one, and the gh-unavailable path lists
     nothing.
   Use fakes for gh and git; no real worktrees.

## Out of Scope
- Deleting anything automatically. Deletion stays the user's (`delete_worktree_or_data`).
- Run-data retention policy for rpg runs (rpg-planner owns its data).
- Changes to `.claude/settings.json`, unless the existing hook entry cannot host the check. If it can't, stop and ask;
  settings.json is a governing file.

## Acceptance Criteria
- AC1: a session whose disk drops below the threshold mid-session sees the warning within 10 minutes of its next tool
  call, without restarting.
- AC2: the hook adds no measurable latency: one statvfs per window, and the tool call never fails.
- AC3: `disk_headroom.py` below the threshold shows the removable-worktrees section, with sizes and the prune command.
- AC4: the tests in Scope 4 pass, and the existing disk_headroom and prune_branches tests still pass.

## Related Tickets
- TCK-20261008-SESSION-DISK-HEADROOM-GUARD (the SessionStart warning); the prune_branches `--worktrees` ticket.

## Related Docs
- docs/guides/ (session layer and environment guide, disk-headroom section).

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES/ (created at close)

## Related Code Areas
- tools/sessions/{disk_headroom,prune_branches,session_start_hook}.py, tools/agent-monitoring/post_tool_hook.py, tests/tools/

## Assumptions / Open Questions
- post_tool_hook.py runs on every tool call in every session, so the throttle is the main design constraint.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
