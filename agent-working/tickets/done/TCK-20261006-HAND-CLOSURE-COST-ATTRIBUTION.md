---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION
phase: done
date: 2026-10-06
tags: [observability, agent-monitoring, process-improvement]
---

# TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION

## Title
Hand closures get `cost_proxy_score` and `tool_call_count` from the tools.jsonl rows that join to them, labelled with provenance

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST`. Depends on `TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS`.
Cost keys are attached only when `tools.jsonl` rows carry the event's `(run_id, seq)` from a live sidecar
(`record_hand_orchestrated_closure.py:433-438`, `compute_tool_stats(..., omit_when_unattributed=True)`).
Hand closures have no sidecar, so their keys are left out. This is the main reason spend-proxy coverage
is 18.3% (W40).

## Scope
1. Use the join key chosen by the design child (`session_id` plus the claim window in `design.md` section 2; ticket ID cannot select rows) to collect the `tools.jsonl` rows that belong to a hand closure. That includes rows with
   `run_id: null`.
2. Compute `tool_call_count` and `cost_proxy_score` with the unchanged `cost_proxy.py` formula. Attach them with a
   provenance marker that says they are derived rather than sidecar-attributed.
3. Never claim one row for two tickets. Concurrent tickets in one session must split rows or leave them
   unclaimed, as the design specifies. Rows already attributed to a sidecar run keep that attribution.
4. When nothing joins, the keys stay absent, as today. Never write 0.

## Out of Scope
- Changing `cost_proxy.py`'s formula or `post_tool_hook.py`'s row shape (beyond what the design requires).
- Token counts from transcripts. They stay local-only.
- Backfilling.

## Acceptance Criteria
1. A fixture hand closure with matching `tools.jsonl` rows gets `tool_call_count` and `cost_proxy_score` equal to
   the hand-computed values, plus the derived provenance marker.
2. A fixture with two concurrent tickets in one session attributes no row twice. Tested.
3. A fixture with no joinable rows leaves both keys absent. Tested; this is the regression guard for
   `TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP`.
4. A sidecar-attributed row is never re-claimed by the derived join. Tested.
5. (design AC) Two hand closures by one session in one activity block: rows before the first closure's end go to it, later rows to the second, and the union has no repeated row. Tested.
6. (design AC) Claimed events carry `cost_source: "session_window"`; sidecar-attributed events carry `cost_source: "sidecar"` or no field, and a row with a sidecar `run_id` is never in a claim. Tested.

## Related Tickets
- `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST` (parent), `TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS` (dependency)
- `TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP`, `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`, `TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT`

## Related Docs
- `docs/agent-monitoring/schema.md` (cost proxy :249-275, tools rows :470-480)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN/design.md` (after child 1 closes)

## Related Code Areas
`tools/agent-monitoring/record_hand_orchestrated_closure.py`, `record_events.py` (`compute_tool_stats`
:95-105, :160-162), `cost_proxy.py` (:29-47, read-only), `post_tool_hook.py` (:73-174, read-only).

## Assumptions / Open Questions
- The design may decide that some rows can never be attributed safely, for example a session with interleaved
  tickets and no ticket-ID evidence. Those rows stay unclaimed, and the retro counts them.

## Implementation Notes
Built on child 2's claim window. The total is carried on the final event that has no sidecar attribution (phases are not resolved; see investigation.md), with `cost_source: "session_window"`; a sidecar path event gets `cost_source: "sidecar"`. Spend-proxy coverage is still capped by the sessions that write no tools rows (TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES).
Hand-filed by agent-working-design (interim planner), 2026-10-06.

## Test Summary
7 new tests in `tests/tools/test_hand_closure_time.py` (32 pass); monitoring sweep 1,517 passed, 1 xfailed.

## Files Changed
`tools/agent-monitoring/hand_closure_time.py`, `record_hand_orchestrated_closure.py`, `record_events.py`, `docs/agent-monitoring/schema.md`, `tests/tools/test_hand_closure_time.py`.

## Completion Summary
A hand closure now carries the cost of its own session's unattributed tool rows as a labelled ticket-level total (session_window), never claiming a row twice and never writing 0 when nothing joins.
