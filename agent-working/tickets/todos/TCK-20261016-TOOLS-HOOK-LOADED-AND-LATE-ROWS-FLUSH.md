---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
phase: open
date: 2026-10-16
tags: [agent-monitoring, hooks, data-quality]
---

# TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

## Title
Say when a session's tool-call hook is not loaded, and get late tool rows committed, so tools shards cover the sessions that close tickets

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Follow-up filed by `TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS` (scope item 4, measured on the W41 data). Only 11 of the 41 distinct sessions that closed W41 runs have any tool row (27%); 94 of 129 run shards have no tools shard; 5438 of 5482 W41 tool rows carry no run_id, so a row joins to a run only by session id. Of the 30 closing sessions without rows, 19 have a transcript on the measuring host: in 14 the transcript shows no trace of `post_tool_hook.py` running (the hook was not loaded in that worktree or session), in 5 it ran and its rows are missing from the committed shards (written after the branch's last commit, or unstaged). So roughly three quarters of the gap is a hook that never ran, and a quarter is rows that never reached a commit.

## Scope
1. Hook not loaded: at SessionStart (and in the freshness line of `TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START`), say when the project hook set in `.claude/settings.json` lacks the PostToolUse monitoring hook for this worktree; report-only. Measure first how the 14 sessions came to run without it (stale worktree, launch outside the repo, hooks disabled).
2. Late rows: decide how a tools row written after a branch's last commit reaches `main`: a commit-time reminder (the pre-push advisory already warns of a dirty shard), or a flush at the next hook call. Pick one with numbers; do not build a second write path.
3. Re-measure the coverage after both and record it beside the 27%.

## Out of Scope
- Back-filling historical rows; changing the shard keying (branch name).
- Editing `.claude/settings.json` (owner's file; put a literal diff in the PR).

## Acceptance Criteria
- The cause of the 14 no-trace sessions is stated with counts.
- A session without the monitoring hook gets one line saying so at start (test with a fixture settings file).
- The late-row decision is recorded with the numbers that support it, and the re-measured coverage is written down.

## Related Tickets
- TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS
- TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START
- TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

## Related Docs
- docs/agent-monitoring/README.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS/

## Related Code Areas
- tools/agent-monitoring/post_tool_hook.py, tools/sessions/settings_freshness.py, tools/sessions/session_start_hook.py

## Assumptions / Open Questions
- The 5-of-19 and 14-of-19 split uses the transcripts present on one host; sessions on other hosts or since purged are not in it.

## Implementation Notes
(filled during work)

## Test Summary
(filled during work)

## Files Changed
(filled during work)

## Completion Summary
(filled at close)
