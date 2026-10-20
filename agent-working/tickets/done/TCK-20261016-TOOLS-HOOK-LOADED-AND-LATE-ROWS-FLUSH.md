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
- (Owner decision 2026-10-21) Back-fill is W43 only: W41 and W42 are not re-closed or back-filled. Lead restored the 809 W43 rows into the main checkout's `main.tools.jsonl`; the week-close sweep picks them up when W43 closes. The side branch `lead-planner-monitoring-shards` is neither merged nor read here.
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
- 2026-10-21 (agent-working-implementer): step 1 measured; see agent-working/staging_artifacts/<ticket>/investigation.md. The data shows no measured case of an unloaded hook on this host (scope 1 stays: it is in the ACs, cheap and report-only). The late-row gap is main-checkout `main.tools.jsonl`, which no PR carries; scope 2 is done in `week_close.py` (planner-approved conditions: read-only on the main checkout via the git common dir, dedup on full-row identity, only the week being closed). It improves row coverage, not the retro's duration coverage (finding 4).

## Test Summary
New: tests/tools/test_week_close_main_checkout_sweep.py (9: append once in ts order with the main checkout file byte- and mtime-identical, idempotent re-run, overlap with canonical and a branch shard counted once, two calls sharing a timestamp both kept, only the closed week and only `main.tools.jsonl`, torn and blank lines skipped, skip reasons, CLI line, `find_main_checkout` through a real git worktree); test_session_settings_freshness.py (5 monitoring-hook-line cases); test_session_resolve_and_hook.py (1 wiring case). The existing week_close, session start and freshness tests pass unchanged. No full tests/tools run.

## Files Changed
- tools/agent-monitoring/week_close.py (`find_main_checkout`, `sweep_main_checkout_tools`, `close_week` and CLI line)
- tools/sessions/settings_freshness.py (`monitoring_hook_loaded`, `monitoring_hook_line`), tools/sessions/session_start_hook.py (one line wired)
- docs/agent-monitoring/README.md
- tests/tools/test_week_close_main_checkout_sweep.py, test_session_settings_freshness.py, test_session_resolve_and_hook.py
- agent-working/stored_artifacts/TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH/ (investigation, plan, test_plan, measure.py, unknown_durations.py, sessions.csv)

## Completion Summary
Measured first: no closing session on this host lacked the hook (the transcript test cannot see a silent hook); the whole measurable gap is the main checkout's `main.tools.jsonl`, which no PR carries. Fixed in `week_close.py` (read-only sweep via the git common dir, full-row dedup, only the closed week). Scope 1 shipped as one report-only SessionStart line, although the data shows no measured case. Re-measured on today's `origin/main`: W41 15/41 and W42 14/29 unchanged (owner: back-fill is W43 only); W43 8/12 becomes 11/12 when W43 closes. The sweep improves row coverage, not the retro's duration coverage: of W43's 41 unknown durations, 17 have no rows, 16 have too few in the activity block (10 closed after a >30 min pause), 4 are back-to-back closures and 4 would derive now; the derivation rules go to the owner as a follow-up. No settings.json change.
