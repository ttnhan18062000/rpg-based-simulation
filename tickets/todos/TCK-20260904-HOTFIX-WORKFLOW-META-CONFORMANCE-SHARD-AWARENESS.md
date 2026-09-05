---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS
phase: open
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS

## Title
workflow_meta_conformance.py still reads the retired flat events.jsonl, not the weekly shard

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found incidentally during `TCK-20260904-REPUTATION-LOCALITY-SCOPE`'s own Finalize phase (its
post-Finalize advisory `workflow_meta_conformance` check reported FAIL for every one of that
ticket's 12 real, correctly-recorded events). Root cause:
`tools/gate_checks/workflow_meta_conformance.py:50` still hardcodes
`DEFAULT_EVENTS_PATH = Path("agent-monitoring/events.jsonl")` — the monolithic flat file retired by
`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC` in favor of
`agent-monitoring/data/<ISO-week>/events.jsonl` shards. Unlike
`tools/gate_checks/done_checker_static.py` (which correctly uses a shard-aware
`_jsonl_rows_for_run_id_across_weeks()` helper for the same lookup, per
`check_monitoring_write_recorded`), this checker's grep scope was never covered by
`TCK-20260902-MONITORING-SHARD-CONSUMERS`' consumer migration — that ticket's own scope was
`tools/agent-monitoring/`'s 4 readers, not `tools/gate_checks/`. This is a distinct gap from
`TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS` (which covered the separate
`tools/agent_codex_*`/`tools/agent_replay_codex/` subsystem's `tools.jsonl` readers, not this
file's `events.jsonl` read).

Confirmed non-blocking today: `implement-ticket.js`'s own post-Finalize call site treats this
check's result as advisory-only (`status` used, never gates ticket close) — so no ticket has been
silently blocked by this, but every standard/epic-tier ticket finalized since the sharding
migration landed has logged a false "possible phase-meta drift" WARNING, which erodes the signal's
value for whoever is meant to act on a genuine drift.

## Scope
- Update `tools/gate_checks/workflow_meta_conformance.py`'s `DEFAULT_EVENTS_PATH` (or the function
  parameters that default to it) to resolve the current-and-recent weekly shard(s) under
  `agent-monitoring/data/<ISO-week>/events.jsonl`, following the same shard-resolution approach
  `done_checker_static.py`'s `_jsonl_rows_for_run_id_across_weeks()` already uses — reuse that
  helper directly if its signature fits, rather than re-implementing shard globbing a third time.
- Add a regression test confirming `check_workflow_meta_conformance()` correctly finds events for a
  run_id whose events live only in a weekly shard, not the (now nonexistent) flat file.

## Out of Scope
- Any other `tools/gate_checks/*.py` module — a full audit of every gate-check script for the same
  stale-path class of bug is a separate concern if warranted, not assumed necessary here.
- The `tools/agent_codex_*`/`tools/agent_replay_codex/` subsystem — already covered by
  `TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS`.

## Acceptance Criteria
- [ ] `check_workflow_meta_conformance(run_id)` correctly locates events for a run_id whose rows
      exist only under `agent-monitoring/data/<week>/events.jsonl`, verified by a new test using a
      fixture run_id with rows only in a weekly shard.
- [ ] Re-running the post-Finalize advisory check against a real, already-DONE ticket from this
      week (e.g. `TCK-20260904-REPUTATION-LOCALITY-SCOPE`) returns `status: "CLEAN"`, not `FAIL`.

## Related Tickets
- TCK-20260904-REPUTATION-LOCALITY-SCOPE (found this gap during its own Finalize)
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC
- TCK-20260902-MONITORING-SHARD-CONSUMERS
- TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS (same class of gap, different subsystem)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- tools/gate_checks/workflow_meta_conformance.py
- tools/gate_checks/done_checker_static.py (shard-aware helper to reuse)

## Assumptions / Open Questions
None.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
