---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES
phase: open
date: 2026-10-06
tags: [agent-monitoring, hooks]
---

# TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES

## Title
About 43% of hand closures have no tools.jsonl shard, which caps derived time and cost coverage

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
While designing TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN, the implementer measured all 238 hand closures in
W40–W41. Only 136 have a tools shard in their worktree at all (`coverage_by_run.csv` in that ticket's stored
artifacts), and tool-activity time is derivable for only 130 (54.6%). The rest is not random. Every derived
duration (that epic's child 2), every session-window cost (child 3) and the delivery-cost watchlist metric
(RETRO-2026-W41: 3 `gh pr create` seen out of 109 merged PRs) is capped by this coverage.

Leading hypothesis, to verify, not assume: most project hooks in `.claude/settings.json` use cwd-relative
commands, e.g. `python3 tools/agent-monitoring/post_tool_hook.py 2>/dev/null || true`. When the session's cwd is
not the repo root, the hook exits non-zero and `|| true` hides it, so the shard is never written. The newer
session-layer hooks resolve `git rev-parse --show-toplevel` first; the older ones do not.

Second candidate: shards are written but never staged in some worktrees, despite the "always stage
agent-monitoring" rule.

## Scope
1. **Investigate first.** For the 102 closures without a shard, establish which cause applies, from session
   transcripts' cwd, the worktree and the branch: launched outside the repo, cwd-relative hook no-op, or written
   but unstaged. Record the split in `investigation.md`.
2. **If the cwd-relative cause holds,** convert the `tools/agent-monitoring/*` hook commands in
   `.claude/settings.json` to the toplevel-resolving form the session-layer hooks already use. Show the owner the
   literal diff first, under the session-layer hold rule.
3. **If the unstaged cause holds,** extend `done_checker_static` (or the closure recorder) to warn when the
   current week's tools shard for the worktree is untracked at close.
4. **If the dominant cause is launching outside the repo,** record that and close against
   TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS. Do not duplicate its fix.

## Out of Scope
- Backfilling W40–W41 shards. The missing data is not recoverable from the repo.
- The epic's derived-time and cost logic (TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS,
  TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION).

## Acceptance Criteria
1. `investigation.md` gives the cause split for the 102 shard-less closures, with counts and the method used.
2. Each confirmed cause has a fix with a test, or an explicit hand-off to the linked ticket.
3. After the fix, a session whose cwd is a subdirectory of a worktree still writes a tools row. Tested by running
   the hook command from a subdirectory with a sample payload.

## Related Tickets
- TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN (source of the 136/238 figure)
- TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION
- TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS
- TCK-20260924-DELIVERY-COST-MEASUREMENT (watchlist row)

## Related Docs
- `agent-working/agent-monitoring/retro/RETRO-2026-W41.md` (Notes, proposal 3)
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN/coverage_by_run.csv`

## Related Code Areas
- `.claude/settings.json` (hook command forms), `tools/agent-monitoring/post_tool_hook.py`,
  `tools/agent-monitoring/pre_tool_hook.py`, `tools/gate_checks/done_checker_static.py`

## Assumptions / Open Questions
- Whether session transcripts record the launch cwd reliably enough for the split. If not, report the share that
  could not be classified.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
