---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
phase: done
date: 2026-10-16
tags: [agent-monitoring, hooks, data-quality]
---

# TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

## Title
Say when a session's tool-call hook is not loaded, and get late tool rows committed, so tools shards cover the sessions that close tickets

## Status
DONE

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
`tools/sessions/settings_freshness.py` gains `monitoring_hook_line` and `unstaged_tool_rows_line`; `session_start_hook.py` prints both on startup/resume/clear (not compact), next to the session-code freshness line. Both are report-only, read-only, and fail open. Measurements and the decision are in `agent-working/stored_artifacts/TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH/investigation.md`. Doc: a section in `docs/agent-monitoring/README.md`. No `.claude/settings.json` change, so there is no literal settings diff for the PR body.

## Test Summary
`pytest tests/tools/test_session_settings_freshness.py tests/tools/test_session_resolve_and_hook.py tests/tools/test_agent_working_paths_guard.py -p no:randomly`: 7 new freshness tests and 1 new wiring test pass; the live `.` worktree gives no hook line and a pending-rows line.
Measured causes (counts): of 41 W41 closing sessions 11 had tool rows on main (27%); of the 19 with a transcript, 8 had rows in an unmerged worktree shard, 6 had no hook event at all, 5 had hook events but no rows. If rows in unmerged worktree shards are counted, 19 of 41 sessions (46%) have rows somewhere.
Re-measure: the new lines affect sessions started after this merges, so coverage after both can only be measured on the next closed week's data (W44 retro); it is not claimed here.

## Files Changed
- `tools/sessions/settings_freshness.py`
- `tools/sessions/session_start_hook.py`
- `tests/tools/test_session_settings_freshness.py`
- `tests/tools/test_session_resolve_and_hook.py`
- `docs/agent-monitoring/README.md`

## Completion Summary
Late rows are decided: a SessionStart reminder, no flush (8 of 19 sessions had rows that only lacked a commit; a flush would add a git-writing second write path; the pre-push check misses older weeks). Hook-not-loaded now says so at start. The earlier 14/5 split relied on a text match transcripts do not support; the corrected split is 8/6/5. Known gaps: the 5 'hook fired, no row' sessions are not provably the silent `test -f` skip; 11 of the 30 uncovered sessions have no transcript on this host; the post-change coverage figure needs a week of data.
