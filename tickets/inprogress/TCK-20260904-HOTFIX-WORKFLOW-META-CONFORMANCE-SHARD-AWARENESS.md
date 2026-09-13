---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS
phase: inprogress
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS

## Title
workflow_meta_conformance.py still reads the retired flat events.jsonl, not the weekly shard

## Status
INPROGRESS

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
- [x] `check_workflow_meta_conformance(run_id)` correctly locates events for a run_id whose rows
      exist only under `agent-monitoring/data/<week>/events.jsonl`, verified by a new test using a
      fixture run_id with rows only in a weekly shard.
      (`test_collect_run_event_statuses_finds_rows_only_in_a_weekly_shard`, plus a second new
      test proving a run whose events straddle two different weekly shards is found in full.)
- [x] Re-running the post-Finalize advisory check against a real, already-DONE ticket from this
      week (e.g. `TCK-20260904-REPUTATION-LOCALITY-SCOPE`) returns `status: "CLEAN"`, not `FAIL`.
      (This module's real status vocabulary is `PASS`/`FAIL`/`NA`, not `CLEAN` — a small
      imprecision in this AC's own wording, not a bug; verified live:
      `check_workflow_meta_conformance('TCK-20260904-REPUTATION-LOCALITY-SCOPE')` →
      `summarize_conformance_results(...)` → `("PASS", "12 declared phase(s) checked, 0 FAIL")`.)

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
Reused `done_checker_static.py::_jsonl_rows_for_run_id_across_weeks` directly, per the ticket's
own instruction, rather than re-implementing shard globbing a third time. Renamed the module's
`DEFAULT_EVENTS_PATH`/`events_path` (a single flat-file path) to `DEFAULT_EVENTS_ROOT`/`data_root`
(a shard-root directory), matching `done_checker_static.py`'s own naming convention for the exact
same underlying concept — confirmed safe: the only production call site
(`implement-ticket.js:1865`) passes `run_id` positionally only, never names the parameter, so the
rename breaks nothing live. Updated every test in `test_workflow_meta_conformance.py` that
constructed a flat-file fixture to write a weekly-shard fixture instead (`tmp_path/<week>/
events.jsonl`), including the pre-existing real-data replay test (`_REAL_EVENTS_PATH` →
`_REAL_EVENTS_ROOT`, now `agent-monitoring/data`) — that test's own precondition assert
(`real_rows` must be non-empty) had been silently vacuous since the flat file was retired (it
would have failed at the wrong assertion, for the wrong reason, while still reporting as an
expected `xfail`); confirmed with `--runxfail` that it now reaches its actual intended assertion
(the documented Security-Review architecture question) rather than an unrelated file-not-found
error.

## Test Summary
```
pytest tests/tools/test_workflow_meta_conformance.py tests/tools/test_done_checker_static.py \
       tests/tools/test_mechanics_auditor_static.py -q
# 156 passed, 1 xfailed
```
Live-verified against real repo data, not just the fixture suite: `check_workflow_meta_conformance`
run directly against 3 real ticket run_ids from this week's shard
(`TCK-20260904-REPUTATION-LOCALITY-SCOPE`, `TCK-20260912-WORKING-LOG-APPEND-HELPER`,
`TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION`) — the first returns clean `PASS`; the
other two correctly flag only the pre-existing, documented Security-Review gap (the same one the
suite's own `xfail` test names), not the old "zero events found for every phase" false positive.

## Files Changed
- `tools/gate_checks/workflow_meta_conformance.py` — shard-aware `DEFAULT_EVENTS_ROOT`,
  `_jsonl_rows_for_run_id_across_weeks` reuse, `events_path`/`data_root` rename.
- `tests/tools/test_workflow_meta_conformance.py` — fixture helper writes shard paths; 2 new
  regression tests (single-shard, cross-shard); real-data replay test's own path updated and
  re-verified to fail for its intended reason again.

## Completion Summary
Fixed the stale flat-file path bug: `workflow_meta_conformance.py` now resolves events across
`agent-monitoring/data/<week>/events.jsonl` weekly shards via the same shard-aware helper
`done_checker_static.py` already uses for the identical lookup, instead of a hardcoded, retired
flat file. Confirmed the false-positive is gone against 3 real tickets' actual event data, not
just synthetic fixtures. Found and fixed a real side effect while touching this file: the existing
`xfail(strict=True)` real-data replay test had been silently failing at the wrong assertion (data
not found, due to the same stale path) rather than its intended one (an unrelated, still-open
Security-Review architecture question) — confirmed with `--runxfail` that it now fails for the
right reason again.
