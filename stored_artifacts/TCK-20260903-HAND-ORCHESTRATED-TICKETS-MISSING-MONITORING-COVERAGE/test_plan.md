---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE
artifact_type: test_plan
tags: [agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE

## Normal flow
- `build_records()` expands a minimal `{phase, status, summary}` event list into a full run record
  + full event-record batch sharing one `run_id`/`execution_id`/`provider`/`ticket_id`, with
  1-indexed sequential `seq` in array order.
- CLI writes exactly one run record and N event records to the current-ISO-week
  `agent-monitoring/data/<week>/{runs,events}.jsonl` shard, matching
  `record_run.py`/`record_events.py`'s own real write target.
- `--final-status`/`--workflow` are overridable (not hardcoded to `DONE`/`implement-ticket`), since
  a real hand-orchestrated closure might be `NEEDS_HUMAN_INPUT` or an `implement-epic` run.

## Edge cases
- Per-event `agent` override respected; unset events fall back to `--agent`'s default.
- `start_ts`/`end_ts` default to "now" (identical value for both, matching this project's own
  existing precedent for hand-orchestrated closures that don't track real elapsed wall-clock time)
  when omitted, but explicit ISO-8601 values are passed through unchanged when given.
- Empty `--events` array is rejected (a closure needs at least one phase recorded).

## Failure modes
- Invalid `--tier` (outside `vocabulary.CANONICAL_TIERS`) rejected by argparse's own `choices`
  before any file write happens.
- An event object missing `phase`/`status`/`summary` is rejected with a clear per-index error
  message, and — critically — no partial write occurs (neither `runs.jsonl` nor `events.jsonl` is
  touched on a validation failure, matching `record_run.py`/`record_events.py`'s own atomic-only-
  on-success contract).
- Malformed `--events` JSON is rejected with a parse error, not a stack trace.

## Regression-prone paths
- The wrapper's expanded output must pass `record_run.py`'s and `record_events.py`'s own real
  `validate_record()` functions unchanged — asserted directly in
  `test_build_records_output_passes_the_real_underlying_validators`, so a future change to either
  underlying module's required-field set is caught here too, not just in that module's own tests.
- `done_ticket_monitoring_coverage.py`'s audit must report a ticket closed via this wrapper as
  `covered` — verified by dogfooding: this ticket's own closure is recorded through the new
  wrapper, then a fresh audit run is checked to confirm `TCK-20260903-HAND-ORCHESTRATED-TICKETS-
  MISSING-MONITORING-COVERAGE` no longer appears in `missing`.

## Commands
- `pytest tests/tools/test_record_hand_orchestrated_closure.py -v`
- `pytest tests/tools/test_record_run.py tests/tools/test_record_events.py -v` (regression check —
  confirm the wrapper's reuse of these modules' functions didn't require touching either file)
- `python3 tools/agent-monitoring/done_ticket_monitoring_coverage.py` (post-closure dogfood check)
