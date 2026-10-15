---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS
phase: open
date: 2026-10-15
tags: [agent-monitoring, hooks, data-quality]
---

# TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS

## Title
Record failed tool calls and stop corrupting tool durations; explain and size the missing tools shards

## Status
OPEN

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
(filled during work)

## Test Summary
(filled during work)

## Files Changed
(filled during work)

## Completion Summary
(filled at close)
