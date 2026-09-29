---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED
phase: open
date: 2026-09-14
tags: [performance, observability]
---

# TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED

## Title
`src/observability/cognition/decision_trace_writer.py::_write_entry_to_file` measured as a real,
material per-tick I/O cost at 1000-entity scale — REPORT ONLY, not investigated

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
**This ticket is a REPORT of an observed measurement, not an investigation and not a diagnosis.**
No root cause was looked at, no fix was attempted or proposed, and nothing here should be read as
implying the cost is a defect, is avoidable, or is unreasonable for what the function does. All that
was done: profile one specific real scenario, notice this function's numbers, write them down.

While investigating an unrelated regression in `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`
(enabling `ENABLE_COMBAT_ENGAGEMENT`, a previously-dormant domain, for the first time), a `cProfile`
run of `src/perf/scenarios.py::build_metropolis_state(entity_count=1000, region_count=50,
buildings_per_region=20)` running 5 real kernel ticks (3 warmup + 5 profiled, single Python process,
this sandbox's hardware) showed:

```
ncalls  tottime  percall  cumtime  percall  function
200     0.054    0.000    1.295    0.006    src/observability/cognition/decision_trace_writer.py:154(_write_entry_to_file)
```

That is ~1.30s of cumulative time across 200 calls (~6.5ms/call) within a 5-tick sample at 1000
entities — file I/O in a hot per-tick path, and the call count (200 over 5 ticks = 40/tick) rose
directly with the same real combat-event increase this investigation measured separately (combat
volume rose 4.1x once `ENABLE_COMBAT_ENGAGEMENT` was live — see the A/B table referenced below):
more real decisions/events to trace naturally means more trace-write calls. Whether the *per-call*
cost itself (not just the call count) is reasonable was not investigated.

For the companion A/B per-phase attribution table (same investigation, same scenario, flag OFF vs
ON, 20 ticks) see `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED` (the natural anchor
for that table) and `performance_m4_baseline_gate_a_epic.md`'s own "Confirmed field evidence" note.
That table shows a new `persistence` phase cost of ~37ms/tick appearing only with the flag ON, and
`advancement` (which includes `_phase_observability()`, the caller of decision-trace writing) rising
+543ms/tick — this function's own contribution to either is not separately isolated in that table.

## Scope
- Determine whether `_write_entry_to_file`'s per-call cost (~6.5ms) is dominated by real disk I/O,
  serialization, or something else, and whether it generalizes beyond this one scenario.
- Determine whether the file-write pattern (frequency, batching, sync vs buffered) is inherent to
  what decision-trace observability requires, or a real optimization opportunity — this ticket does
  not presuppose either answer.
- If a real opportunity is confirmed, route it through the existing performance-optimization epic's
  own Gate-A process (likely `PERF-M5-T05`, "Snapshot/freeze/serialization/IPC improvement," in
  `performance_m5_exact_optimization_delivery_epic.md`, once ranked) rather than as a standalone fix
  decided from this one measurement.
- Cross-check against M3's own observer-overhead exit criteria
  (`performance_m3_phase_observability_foundation_epic.md`: "overhead is quantified and heavy runs
  are not promoted as clean baselines") — this is exactly the kind of observer-cost M3 intends to
  make routine to quantify.

## Out of Scope
- Any fix or optimization attempt — none was investigated, and none is authorized by this ticket.
- Whether decision-trace observability itself should exist or be gated differently — out of scope;
  this ticket is about its measured cost, not its purpose.

## Acceptance Criteria
- A real investigation establishes what dominates the per-call cost and whether it is material at
  realistic corpus-world scale and realistic trace-event volume.
- If a candidate optimization is confirmed, it is routed into the performance-optimization epic's
  Gate-A process rather than fixed ad hoc.
- If it is not material at realistic scale, or the cost is inherent, that conclusion is recorded
  here and the ticket closes on that finding.

## Related Tickets
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` — where this was observed.
- `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED` — carries the full A/B per-phase
  attribution table from the same investigation.
- `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED` — a third unrelated system cost from the same
  profiling run.
- `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT` — a genuinely diagnosed defect from the same
  investigation, kept separate since it's a different kind of finding.

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_m5_exact_optimization_delivery_epic.md`
  (PERF-M5-T05)
- `docs/plans/design_enhancement/performance_optimization/performance_m3_phase_observability_foundation_epic.md`
  (observer-overhead quantification, PERF-M3-T07)

## Related Code Areas
- `src/observability/cognition/decision_trace_writer.py::_write_entry_to_file`

## Assumptions / Open Questions
- Whether 40 trace writes/tick at 1000 entities is representative of any real corpus profile's own
  decision-trace volume — not checked.

## Implementation Notes
_(not applicable — report-only ticket, no implementation performed)_

## Test Summary
_(not applicable — report-only ticket, no implementation performed)_

## Files Changed
_(none — report-only ticket)_

## Completion Summary
_(pending future investigation)_
