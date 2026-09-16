---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION

## Title
`monitoring_integrity_backlog_check`'s item-2 ratchet counts frozen historical debt and brand-new regressions in one number, so a failure cannot be read without an investigation — and the obvious fix for it is the wrong one

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Found 2026-09-15, immediately after `TCK-20260915-MONITORING-INTEGRITY-BACKLOG` landed its ratchet,
when the user asked a reasonable question about the constant: *"is that we need to update every
ticket landed?"*

The check failed with:

```
FAIL: working_log DONE rows with no run record (item 2): 219 exceeds the ratchet ceiling (218) by 1
```

**That failure is correct and valuable** — three of the monitoring-anomaly epic's own tickets
(`MONITORING-INTEGRITY-BACKLOG`, `MONITORING-ANOMALY-VALIDATOR`,
`RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES`) closed with zero run records *and* zero event rows,
i.e. `record_hand_orchestrated_closure.py` was never run for them despite CLAUDE.md's After Work
rule requiring it. The ratchet caught a real, current process miss on its first outing.

**The problem is that the number cannot be read.** Item 2's count is
`historical_debt + live_regressions` in a single integer:

- ~216 rows are pre-existing, unreconstructable debt nobody is going to backfill (it spans
  2026-03 → 2026-09; 462 further rows predate the check's own `MONITORING_START` cutoff entirely).
- 3 rows are a live process miss from today, fixable in minutes.

A reader seeing `219 exceeds 218 by 1` cannot tell which they are looking at. Establishing it took
four separate corpus queries. **The failure mode that follows is predictable**: the cheapest
resolution looks like raising the ceiling to 219, which is exactly what the constant's own comment
forbids ("Raising any of them to paper over a newly-introduced instance defeats the point of this
check") — and it would silence the mechanism on the first real thing it ever caught. A gate whose
correct response requires an investigation, and whose incorrect response is a one-character edit,
will eventually be resolved the wrong way by someone in a hurry.

This is a variant of the pattern this whole arc has been cataloguing, one step removed: not a
mechanism that fails to measure, but a mechanism that measures correctly and reports
uninterpretably.

## Scope
- Split item 2 into two conditions with different semantics:
  - **Frozen historical debt** — rows on/after `MONITORING_START` but before a new freeze date
    (the date this ticket lands). Ratcheted, may only decrease, expected to sit still forever.
  - **Live coverage** — rows after the freeze date. This should be **zero-tolerance**: any DONE
    working_log row written after the freeze with no run record is a process miss that is always
    fixable by running `record_hand_orchestrated_closure.py`, so a non-zero count is always
    actionable and never historical.
- Make each condition's evidence string say which kind it is, and — for the live condition — name
  the offending ticket ids directly, so the fix is obvious from the failure text without any
  investigation.
- Consider whether the same split applies to the other three conditions (unusable `ts`, unknown-week
  rows). Evidence so far says they are purely historical (all W24–W27 / June-era), so they may
  legitimately stay single-valued — confirm rather than assume.

## Out of Scope
- Backfilling the ~216 historical rows. They are unreconstructable; that was settled by
  `TCK-20260915-MONITORING-INTEGRITY-BACKLOG`.
- Fixing the three uncovered epic closures — that is immediate remediation happening now, not this
  ticket's work. This ticket assumes they are already recorded and the count is back at ~216.
- ~~The other ratchets introduced by the anomaly epic (duplicate runs, seq integrity, tool-call
  mismatch, vocabulary drift). If any shares this conflation shape, note it here rather than
  widening scope.~~ **Superseded 2026-09-16 — see "Scope widened" below. Two of them demonstrably
  share the shape, so treating them as out of scope would fix one instance of a five-instance
  pattern.**

## Scope widened — 2026-09-16 (user decision)

The original Out-of-Scope line above assumed the other ratchets probably did not share this
conflation. **One day of real operation disproved that.** Five checks now demonstrably move on
*legitimate activity* rather than on regression:

| Check | What moved it | Cost |
|---|---|---|
| `no-run-record` (item 2) | historical debt + live misses in one integer | the original finding |
| `working_log_duplicate` (84→85) | a legitimate `BLOCKED`→`DONE` reopen | re-pin |
| `event_seq_integrity` (71→72) | the same reopen | re-pin |
| `ATTRIBUTION_RATE_FLOOR` | hand-orchestrated work (a sanctioned mode) | **gate deleted** |
| `CITATION_RESOLUTION_FLOOR` | closing one ordinary ticket (pop. 83→82) | **broke `main`'s CI** |

The generalisation, in the user's words (2026-09-16): *"we don't need to make the test too strictly
for agent working, since it's just the side effect, not the core simulation feature."* And the
sharper diagnostic framing, from `rpg-feature-planning`: **a check that fails on legitimate activity
is not a weak signal, it is an inverted one — it fires *because* work is happening.**

**What this adds to this ticket's scope:**

- Treat `working_log_duplicate` and `event_seq_integrity` as in scope. A legitimate two-phase
  closure must not consume ratchet headroom in any of them; today it consumed headroom in two.
- Apply the same test to every remaining ratchet in `tools/gate_checks/`: **does its value move
  when nothing is wrong?** If yes, it is inverted and the disposition is to stop gating, not to
  tune the threshold.
- Prefer **removing the gate and keeping the reported number** over splitting the metric, where the
  measurement is genuinely useful. That is what the attribution floor's deletion established as
  precedent, and it is cheaper and more honest than a two-condition split that still needs pinning.
- The split-the-metric design in this ticket's original Scope remains valid *only* where a check
  genuinely mixes frozen historical debt with live regressions (`no-run-record` is the clear case).
  Do not apply it mechanically to the inverted ones.

**Two checks that are NOT in scope and should stay ratcheted**, so this does not become a general
deratcheting exercise: `tool_call_count_mismatch` and `vocabulary_drift` both count corpus debt that
grows only through a real mistake, and neither moved on any legitimate activity during this period.
Ratchets remain the right tool for that shape.

`TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE` handles the citation floor separately and is already
scoped; do not duplicate it here.

## Acceptance Criteria
- [x] Item 2 reports at least two distinct conditions: frozen historical debt (ratcheted) and
      post-freeze live coverage (zero-tolerance).
- [x] The live condition's failure evidence names the specific offending `ticket_id`s.
- [x] A test proves the live condition fails on a planted post-freeze uncovered closure, and that
      the historical condition is unaffected by it.
- [x] A test proves a pre-freeze row does **not** trip the live condition.
- [x] The historical ceiling is re-derived at implementation time and set to the then-current
      measured value: 219 (measured at implementation time against the live corpus — the three
      epic closures were already recorded before this measurement, matching the ticket's own
      Implementation Notes expectation; live reads 0).

### Widened scope — acceptance
- [x] `working_log_duplicate_check.py`'s gate removed (kept `compute_working_log_duplicate_ticket_ids()`
      as a report-only measurement) — a legitimate two-phase reopen moves the count and can no
      longer fail CI.
- [x] `event_seq_integrity_check.py`'s gate removed for both conditions (duplicate-seq and gap) —
      the module's own pre-existing docstring already established both are dominated by the same
      legitimate multi-invocation mechanism; kept as a report-only measurement.
- [x] `tool_call_count_mismatch_check.py` and `vocabulary_drift` (in `monitoring_anomaly_validator.py`)
      left untouched — confirmed neither moved on any legitimate activity during this period; per
      the explicit guard against this becoming a general deratcheting exercise.

## Related Tickets
- `TCK-20260915-MONITORING-INTEGRITY-BACKLOG` (done) — introduced the ratchet this refines
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (done) — the parent epic
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done) — the original
  coverage gap; this ticket's live condition is what would have caught its recurrence immediately
- `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` (open) — sibling case of a
  gate whose arithmetic makes the wrong response cheaper than the right one

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`
- `CLAUDE.md` — After Work, the `record_hand_orchestrated_closure.py` requirement

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MONITORING-INTEGRITY-BACKLOG/`

## Related Code Areas
- `tools/gate_checks/monitoring_integrity_backlog_check.py`
  (`NO_RUN_RECORD_HISTORICAL_CEILING`, `NO_RUN_RECORD_LIVE_CEILING`, `FREEZE_DATE`,
  `MONITORING_START`, `find_working_log_rows_missing_run_record`)
- `tests/tools/test_monitoring_integrity_backlog_check.py`
  (`test_real_corpus_is_at_or_below_all_five_conditions` — the CI-gating pin)
- `tools/gate_checks/working_log_duplicate_check.py` (widened scope: gate removed)
- `tests/tools/test_working_log_duplicate_check.py`
- `tools/gate_checks/event_seq_integrity_check.py` (widened scope: gate removed)
- `tests/tools/test_event_seq_integrity_check.py`

## Assumptions / Open Questions
- The freeze date should probably be this ticket's own landing date, but an argument exists for
  `TCK-20260903`'s date (when hand-orchestrated coverage was first required) — that would classify
  more rows as "live" and might surface real, still-fixable misses. Worth measuring before choosing.
- Whether the live condition should be zero-tolerance or a small ratchet depends on whether every
  post-freeze miss is genuinely always fixable. The three found today were; that is a sample of
  three.

## Implementation Notes
Reproduce the motivating failure by running the check against the corpus before the three epic
closures are recorded. After they are recorded, item 2 should read ~216 and pass.

## Test Summary
- `pytest tests/tools/test_monitoring_integrity_backlog_check.py -v`: 22 passed — includes
  `test_item2_live_condition_fails_on_any_planted_post_freeze_miss_and_names_the_ticket` (planted
  post-freeze row → live FAILs, names the ticket_id, historical PASSes unaffected) and
  `test_item2_live_condition_unaffected_by_a_pre_freeze_row` (pre-freeze row → live stays PASS).
- `pytest tests/tools/test_working_log_duplicate_check.py -v`: 5 passed — includes
  `test_a_legitimate_reopen_moves_the_count_but_cannot_fail_ci`, simulating the exact BLOCKED→DONE
  two-phase closure that consumed ratchet headroom on 2026-09-14.
- `pytest tests/tools/test_event_seq_integrity_check.py tests/tools/test_monitoring_anomaly_validator.py -v`:
  20 passed — confirms `monitoring_anomaly_validator.py`'s own aggregate (which imports
  `check_event_seq_integrity` directly) needed zero code changes, since it just reads the returned
  PASS/FAIL shape.
- Confirmed via direct grep before touching either file: `tool_call_count_mismatch_check.py` and
  `vocabulary_drift` (in `monitoring_anomaly_validator.py`) are not referenced by this ticket's own
  changes and were not edited — matches the explicit guard against general deratcheting.
- Full `pytest tests/tools/ -m "not slow and not extra_slow"` (run together with this batch's other
  three tickets): 2735 passed, 0 failed.

## Files Changed
- `tools/gate_checks/monitoring_integrity_backlog_check.py` — item 2 split into
  `NO_RUN_RECORD_HISTORICAL_CEILING` (ratchet, re-derived to 219) and
  `NO_RUN_RECORD_LIVE_CEILING` (zero-tolerance, names offending ticket_ids in evidence);
  `find_working_log_rows_missing_run_record()` now returns `(historical, live)`;
  `check_monitoring_integrity_backlog()` returns 5 conditions instead of 4.
- `tests/tools/test_monitoring_integrity_backlog_check.py` — rewritten for the split return shape;
  added historical/live-specific tests per the ticket's own Acceptance Criteria.
- `tools/gate_checks/working_log_duplicate_check.py` — removed `DUPLICATE_TICKET_ID_CEILING` and
  the blocking path; added `compute_working_log_duplicate_ticket_ids()` (measurement only);
  `check_working_log_duplicate_ticket_ids()` now always reports PASS.
- `tests/tools/test_working_log_duplicate_check.py` — rewritten for the report-only shape.
- `tools/gate_checks/event_seq_integrity_check.py` — removed `DUPLICATE_SEQ_CEILING`/`GAP_CEILING`
  and both blocking paths; `check_event_seq_integrity()` now always reports PASS for both
  conditions, same two-condition shape `monitoring_anomaly_validator.py` already expects.
- `tests/tools/test_event_seq_integrity_check.py` — rewritten for the report-only shape.
- `Makefile` — reworded `working-log-duplicate-check` and `event-seq-integrity-check` targets'
  help text to "Report ... non-blocking".

## Completion Summary
Item 2 split as originally scoped (historical ratchet + live zero-tolerance, naming offending
tickets directly). The widened scope's own generalization — "does this check's value move when
nothing is wrong?" — was applied to `working_log_duplicate_check` and `event_seq_integrity_check`,
both confirmed by their own pre-existing docstrings to move on ordinary legitimate reopens; both
gates removed, both measurements kept. `tool_call_count_mismatch` and `vocabulary_drift` were
deliberately left untouched, per the explicit guard against this becoming a general deratcheting
exercise — neither moved on legitimate activity during this period.
