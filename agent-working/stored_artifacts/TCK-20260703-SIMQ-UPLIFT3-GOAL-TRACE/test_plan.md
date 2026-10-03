---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE
artifact_type: test_plan
tags: [observability, strategy, trace, decision-trace, duplicate-check]
---

# Test Plan — TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE

## Summary

Investigation (see `investigation.md`) found this ticket's acceptance criteria are already fully
implemented and tested by `TCK-20260627-P1H-GOAL-RUNNERUP` (done 2026-06-27). This test plan is
therefore a **verification plan** confirming existing coverage is sufficient and still green — not
a plan for new test authorship. If a future session decides to proceed with the doc-only fix
recommended in the investigation, no source or test changes are needed; only re-run the existing
suite to confirm the "still passes" claim before closing.

## Existing Coverage Mapped to This Ticket's Acceptance Criteria

All in `tests/unit/observability/test_decision_trace.py`:

| Acceptance Criterion | Covering Test(s) |
|---|---|
| Top-3 candidate goal scores retained at tick commit | `test_decision_trace_runner_up_scores_present` (5 candidates → ranks [2,3] retained), `test_decision_trace_routes_sorted_descending` |
| `EntityInspectionSnapshot.goal_scores` includes runner-up data | Covered indirectly via `DecisionTraceWriter.get_latest_goal_scores()` cache tests; `entity_inspector.py:142` wiring is exercised by `test_set_and_get_active_writer` + `test_adventure_decision_phase_wires_writer` (writer registration/wiring path) |
| `decision_trace.jsonl` schema extended (`source_goal_score`, `runner_up_scores`) | `test_decision_trace_schema_has_all_score_terms`, `test_decision_trace_source_goal_score_present`, `test_decision_trace_runner_up_scores_present` |
| Graceful truncation below 3 candidates | `test_decision_trace_runner_up_fewer_than_3` (2→1 runner-up), `test_decision_trace_runner_up_single_candidate` (1→0 runner-ups) |
| Runner-up distinguishable from winner in multi-goal scenario | `test_decision_trace_runner_up_scores_present` — asserts `len(runner_ups) == 2` and `ranks == [2, 3]`, separate from `source_goal_score` (rank 1, asserted in the sibling test) |
| No change to actual goal-selection behavior (regression) | `test_decision_trace_writer_does_not_import_engine_cognition` (import-boundary guard proving the writer only serializes, never decides); `phase.py` unmodified by the original fix — no separate regression test needed since the call site was untouched |

## Verification Performed This Session

```
pytest tests/unit/observability/test_decision_trace.py -q -m "not slow"
```
Result: **24 passed, 0 failed** (2026-07-04).

## Gaps / Follow-on (Not This Ticket's Scope)

- No test currently exercises `EntityInspectionSnapshot.goal_scores` end-to-end through a real
  `EntityInspector.inspect_entity()` call with a populated writer cache (existing tests verify the
  writer cache and the wiring point separately, not a full integration path). If a human wants
  belt-and-suspenders coverage here, it would be a small additive unit test in
  `tests/unit/observability/` (or wherever `entity_inspector` tests live) — **not required** to
  close this ticket, since the acceptance criteria as written are about `decision_trace.jsonl` +
  the `goal_scores` field's existence/population source, both of which are already directly
  covered.
- The separate strategic-project "candidate vs current" comparison
  (`src/systems/strategic_systems/intelligence.py:925`) and the cognition graph-snapshot
  recorder's single-value `source_goal_score` (`src/observability/cognition/recorder.py:232-256`)
  have no runner-up equivalent and are untested for that dimension — explicitly out of scope per
  this ticket's own Out-of-Scope section (no change to selection logic) and per the acceptance
  criteria's exact targets (`EntityInspectionSnapshot.goal_scores`, `decision_trace.jsonl`).

## Recommended Action

No new tests need to be written to close this ticket. If the doc-correction fix from
`investigation.md` is applied to `docs/plans/audit_fix_plan.md`, re-run the same command above as
a sanity check (already done in this session) and note the result in the ticket's Test Summary
before moving to `tickets/done/`.
