---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS
phase: done
date: 2026-10-06
tags: [observability, agent-monitoring, process-improvement]
---

# TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS

## Title
The hand-closure recorder writes real start and end times with a provenance field, and null rather than 0 when there is no evidence

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST`. Depends on `TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN`.
Today `build_records` in `record_hand_orchestrated_closure.py` sets `now` once (:196). It writes
`start_ts`/`end_ts` as `start_ts or now`/`end_ts or now` (:204-205) and every event `ts` as `now` (:224), so
`duration_s` is 0 (:431). That 0 is recorded as if it were a measurement.

## Scope
1. Implement the time source chosen in the design child's `design.md`. Precedence: values the closer declares
   with `--start-ts`/`--end-ts`, then the derived source, then unknown.
2. Add the provenance field from the design (working name `duration_source`) to run records, using the design's
   vocabulary. When the source is unknown, `duration_s` is null, not 0. `start_ts` is null or equal to
   `end_ts`, as the design specifies.
3. When the design adds `session_id` to runs and events, stamp it from `CLAUDE_CODE_SESSION_ID`. RHC already
   reads that variable at :280 and :332.
4. Event `ts` values keep the closure time unless the closer passes one (design decision: per-event times are not derived),
   with the provenance recorded.
5. Update `docs/agent-monitoring/schema.md` (runs and events field tables) and `record_run.py`/`record_events.py`
   validation for the new fields. Keep old rows valid: the new fields are optional on read.

## Out of Scope
- Cost attribution (child 3) and retro changes (child 4).
- Backfilling past rows.
- Any blocking behaviour. A failure to derive falls back to `unknown`; it never fails the closure (monitoring
  write failure never fails the workflow).

## Acceptance Criteria
1. With no evidence, a hand closure records the unknown provenance and `duration_s: null`. A test pins this.
2. With declared timestamps, provenance is `declared` and `duration_s` equals end minus start. Tested.
3. With derived evidence, provenance names the source and the duration matches a fixture. Tested.
4. A negative or inverted span is never written as a duration. It follows `TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG`'s rule (null). Tested.
5. Existing rows without the new fields still load in `generate_retro.py` and in the integrity report. Tested.
6. (design AC) With no declared times and fewer than 3 claimable rows, a hand closure writes `duration_source: "unknown"`, `duration_s: null`, `start_ts == end_ts`. Tested.
7. (design AC) A fixture `tools.jsonl` with 5 rows of the closing session writes `duration_source: "tool_activity"`, `start_ts` = the first row's `ts` and `duration_s` = the span; a row of another `session_id` or with a non-null `run_id` is ignored. Tested.

## Related Tickets
- `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST` (parent), `TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN` (dependency)
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE`, `TCK-20260929-RUN-EXECUTION-MODE-FIELD`

## Related Docs
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN/design.md` (after child 1 closes)

## Related Code Areas
`tools/agent-monitoring/record_hand_orchestrated_closure.py`, `record_run.py` (`compute_duration_s` :29-62),
`record_events.py`, and the tests under `tests/tools/` for these modules.

## Assumptions / Open Questions
- The exact field names and vocabulary come from the design child. The names used here are working names.

## Implementation Notes
Implemented from the design child's `design.md`: new `hand_closure_time.py`, stamping in `record_hand_orchestrated_closure.py`, optional-field validation in `record_run.py`/`record_events.py`, schema.md rows. `MIN_CLAIMED_ROWS = 3`; `--end-ts` alone bounds the derivation. Decision beyond the design: a declared span that is negative degrades to `unknown`, so a null duration never carries a `declared` label.
Hand-filed by agent-working-design (interim planner), 2026-10-06.

## Test Summary
`tests/tools/test_hand_closure_time.py` 25 passed; sweep over monitoring/record/retro tests 1,303 passed, 1 xfailed.

## Files Changed
`tools/agent-monitoring/hand_closure_time.py` (new), `record_hand_orchestrated_closure.py`, `record_run.py`, `record_events.py`, `docs/agent-monitoring/schema.md`, `tests/tools/test_hand_closure_time.py` (new).

## Completion Summary
Hand closures now record the closing session, the source of their start (declared, tool_activity or unknown) and a null duration when there is no evidence, instead of a 0 that reads as a measurement.
