---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS
phase: done
date: 2026-10-15
tags: [agent-monitoring, hooks, data-quality]
---

# TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS

## Title
Record failed tool calls and stop corrupting tool durations; explain and size the missing tools shards

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, finding 3. In W41 + W42 all 6,957 tools rows have `status: ok`: `post_tool_hook.py` marks a failure only
from `tool_response.is_error`, and no PostToolUseFailure hook is wired, so failed calls (e.g. the 2026-10-15 gh TLS handshake
timeouts and 502s) leave no trace. `duration_ms` is computed from one shared, cwd-relative `.claude/.tool_start` written by
`pre_tool_hook.py` (around L12-13) and read back unkeyed (`post_tool_hook.py` around L78-85). Concurrent sessions corrupt it:
e.g. a `cat` at 8.6 h, 26 calls over 1 h in W41. Coverage is also thin: only 4 `gh pr create` rows against 161 merged W41 PRs,
94 of 129 W41 run shards have no tools shard, and hand-closure durations are known only for agent-working sessions (38 of
274 in W41, 11 of 56 in W42). The Measurement Watchlist row (gh_calls_per_pr) can't be checked until this is fixed.

## Scope
1. Failure rows: wire PostToolUseFailure (or the equivalent payload) to write `status: failed` with a short error class.
   The `.claude/settings.json` edit is the owner's: put the literal diff in the PR body for the owner to apply or approve.
2. Key the start stamp by session_id + tool_use_id (or carry it in the payload), so concurrent and parallel calls can't
   cross. Durations that can't be paired become null, never a wrong number.
3. Readers (retro, delivery-cost tool) treat pre-field `duration_s: 0` hand-closure rows (75 in W41) as unknown.
4. Measure why most role sessions leave no committed tools shard (rows written after a branch's last commit? hook not
   loaded in some worktrees?). Report the cause with numbers and propose the fix as a follow-up ticket (don't build it here).

## Out of Scope
- Building the flush/commit path for late tool rows (follow-up after item 4).
- Back-filling historical rows.

## Acceptance Criteria
- Tests: a failure payload writes one `failed` row; two interleaved fake calls with different tool_use_ids get their own
  durations; an unpairable call gets null.
- The retro's duration sections show the 75 W41 zero rows as unknown after regeneration.
- The ticket records the missing-shard cause with counts, and the follow-up is filed.
- The owner-applied settings diff is in the PR body.

## Related Tickets
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
- TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST
- TCK-20260924-DELIVERY-COST-MEASUREMENT

## Related Docs
- docs/agent-monitoring/README.md (Measurement Watchlist)
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/agent-monitoring/pre_tool_hook.py, tools/agent-monitoring/post_tool_hook.py, tools/agent-monitoring/generate_retro.py
- .claude/settings.json (owner applies)

## Assumptions / Open Questions
- Open: does this Claude Code version emit PostToolUseFailure? Verify against the docs and a live payload before designing around it.

## Implementation Notes
Hooks: `post_tool_hook.py` handles `PostToolUseFailure` (payload `hook_event_name`, `error`, `is_interrupt`, optional `duration_ms`): a failed call writes `status: failed` plus `error_class`, a closed set (`exit_<N>`, timeout, tls, http_5xx, permission, not_found, interrupt, error), never the raw error text; the old `is_error` path also writes the class. `pre_tool_hook.py` no longer writes the shared `.claude/.tool_start`; it writes `.claude/tool_starts/<session_id>.<tool_use_id>` (ids reduced to a safe file-name alphabet); the post hook uses the payload's own `duration_ms` if present, else reads and deletes its own stamp, else null; an unpairable call (no tool_use_id, no stamp) is null; stamps older than 24 h are swept; `.claude/tool_starts/` is gitignored. Whether Claude Code emits PostToolUseFailure and what it carries was checked against the hooks documentation (a claude-code-guide agent): the event exists for calls that started executing and failed, with `tool_use_id`, `error` (first line `Exit code N` for Bash), `is_interrupt` and `duration_ms`; the docs do not state that tool_use_id is identical across Pre and Post, and do not document `tool_response` for a failing Bash call, so the design does not rely on either: an unmatched id gives null. Readers: `retro_provenance.source_of()` counts a pre-field hand closure with a 0 or missing duration as unknown (never averaged); on W41's canonical runs that is 73 rows (the ticket said 75), unknown 163 to 236. `.claude/settings.json` is the owner's: the literal diff to register the hook is in the PR body. The `tools.jsonl` schema doc is updated. Missing tools shards, measured on the W41 data (scope item 4): of 129 run shards 94 have no tools shard and 46 tools shards have no run shard (seat, idle, sync and planning branches: sessions with no ticket closure); 5438 of 5482 W41 tool rows carry no run_id, so the join to a run is by session id; 201 of 281 runs carry a session id, 41 distinct closing sessions, only 11 of them have any tool row (27%). Of the 30 without, 19 have a transcript on this host: in 14 the transcript shows no trace of `post_tool_hook.py` running (hook not loaded in that worktree or session) and in 5 it ran but its rows are not in the committed shards. So about three quarters of the gap is the hook not running, the rest rows that never got committed. The proposed fix is the follow-up TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH (not built here).

## Test Summary
`tests/tools/test_tool_telemetry_failures_and_durations.py` (new, 17 cases: failed row and class set, interrupt, ok rows have no class, interleaved calls from two sessions get their own durations, a stamp is used once, an unpairable call gets null, the shared file is gone, stale stamps swept, hostile ids stay inside the directory) and the existing `test_post_tool_hook.py` (22) pass; `tests/tools/test_retro_provenance.py` (2 new, 3 expectations updated for the intended reclassification of H-OLD from unlabelled to unknown) pass.

## Files Changed
tools/agent-monitoring/pre_tool_hook.py, tools/agent-monitoring/post_tool_hook.py, tools/agent-monitoring/retro_provenance.py, tools/agent-monitoring/generate_retro.py, docs/agent-monitoring/schema.md, .gitignore, tests/tools/test_tool_telemetry_failures_and_durations.py, tests/tools/test_retro_provenance.py; owner applies: .claude/settings.json (diff in the PR body)

## Completion Summary
Failed tool calls leave a row with a short error class once the owner registers PostToolUseFailure; durations are per call or null; the 73 pre-field zero hand closures of W41 read as unknown. The missing-shard cause is measured and a follow-up is filed.
