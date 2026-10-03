---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED
phase: open
date: 2026-09-14
tags: [performance]
---

# TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED

## Title
`src/core/state.py::fingerprint()` measured as a real, material per-call cost at 1000-entity
scale — REPORT ONLY, not investigated

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
3       0.001    0.000    2.828    0.943    src/core/state.py:1545(fingerprint)
```

That is ~2.83s of cumulative time across only 3 calls (~943ms/call) within a 5-tick sample at
1000 entities — a very large per-call cost, though the low call count (3 in 5 ticks) means it is
not called every tick in this scenario; which real caller invokes it, and at what real cadence in
production, was not investigated.

For the companion A/B per-phase attribution table (same investigation, same scenario, flag OFF vs
ON, 20 ticks) see `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED` (the natural anchor
for that table) and `performance_m4_baseline_gate_a_epic.md`'s own "Confirmed field evidence" note.
That table does not separately break out `fingerprint()` — it is folded into one or more of the
named pipeline phases (most likely `advancement` or `resolution_overhead`, both of which include
apply/hash/checkpoint-adjacent work) — which phase specifically was not determined here.

## Scope
- Determine which real call site(s) invoke `fingerprint()`, at what cadence, and whether the
  ~943ms/call figure generalizes beyond this one scenario.
- Determine whether this is inherent to what full-state fingerprinting requires (a real, unavoidable
  hashing cost over 1000 entities) or a real optimization opportunity (e.g. incremental/hierarchical
  hashing) — this ticket does not presuppose either answer. Note: PERF-M5-T04 in
  `performance_m5_exact_optimization_delivery_epic.md` already names "Hierarchical/incremental
  hashing" as a conditional candidate family, gated on "PERF-D5 permits it and flat hashing is
  material" — this observation may be relevant evidence for that gate once formally evaluated, not
  a decision that it applies.
- If a real opportunity is confirmed, route it through the existing performance-optimization epic's
  own Gate-A process, not as a standalone fix decided from this one measurement.

## Out of Scope
- Any fix or optimization attempt — none was investigated, and none is authorized by this ticket.
- Determinism/hash-policy questions already tracked under M1 (`PERF-M1-T03` hash-policy
  reconciliation) — this ticket is about cost, not correctness.

## Acceptance Criteria
- A real investigation establishes the real call site(s), cadence, and whether this is material at
  realistic corpus-world scale.
- If a candidate optimization is confirmed, it is routed into the performance-optimization epic's
  Gate-A process (PERF-M5-T04 or another family, as the investigation supports) rather than fixed
  ad hoc.
- If it is not material at realistic scale, or the cost is inherent, that conclusion is recorded
  here and the ticket closes on that finding.

## Related Tickets
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` — where this was observed.
- `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED` — carries the full A/B per-phase
  attribution table from the same investigation.
- `TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED` — a third unrelated system cost from the same
  profiling run.
- `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT` — a genuinely diagnosed defect from the same
  investigation, kept separate since it's a different kind of finding.

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_m5_exact_optimization_delivery_epic.md`
  (PERF-M5-T04)
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md`
  (PERF-M1-T03, hash-policy — a correctness question, distinct from this ticket's cost question)

## Related Code Areas
- `src/core/state.py::fingerprint()`

## Assumptions / Open Questions
- Which real caller(s) invoke `fingerprint()` and at what cadence — not identified.
- Whether 1000 entities is representative of any real corpus profile — not checked.

## Implementation Notes
_(not applicable — report-only ticket, no implementation performed)_

## Test Summary
_(not applicable — report-only ticket, no implementation performed)_

## Files Changed
_(none — report-only ticket)_

## Completion Summary
_(pending future investigation)_
