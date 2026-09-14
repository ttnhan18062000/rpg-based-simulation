---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED
phase: open
date: 2026-09-14
tags: [performance, social]
---

# TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED

## Title
`src/domains/cooperation/services.py::find_pending_incoming_offer` measured as a real, material
per-tick cost at 1000-entity scale — REPORT ONLY, not investigated

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
4500    1.152    0.000    2.033    0.000    src/domains/cooperation/services.py:27(find_pending_incoming_offer)
```

That is ~2.0s of cumulative time across 4500 calls within a 5-tick sample at 1000 entities — a
material share of that sample's total ~7.9s runtime.

**Companion A/B measurement (this is the natural anchor for this table — cross-referenced from
`TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED` and
`TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`, and mirrored in
`performance_m4_baseline_gate_a_epic.md`'s own "Confirmed field evidence" note).** Same
`build_metropolis_state(1000, 50, 20)` scenario, 20 real kernel ticks measured after 3 warmup
ticks, single process, `ENABLE_COMBAT_ENGAGEMENT` OFF vs ON, reading `kernel._phase_costs` summed
per tick and an `_event_listeners` hook counting real events. **This is a one-scenario measurement,
not a baseline** — not repeated, does not control for this sandbox's own hardware/load variance,
one entity count, one world shape, one seed.

Combat-related events over 20 ticks: 72 (OFF) -> 297 (ON), a 4.1x rise — entities engage/avoid via
`CombatPosture` for the first time, so materially more combat happens. Total events: 3086 -> 12697
(4.1x). Total wall time: 5.37s (269ms/tick) -> 27.30s (1365ms/tick).

Per-phase cost, ms/tick (OFF -> ON, delta):

| Phase | OFF | ON | Delta (ms/tick) | Share of total delta |
|---|---|---|---|---|
| `advancement` | 41 | 584 | +543 | ~50% |
| `resolution_overhead` | 162 | 527 | +366 | ~33% |
| `cooperation` | 160 | 327 | **+167** | ~15% |
| `combat_engagement` (new phase) | 0 | 198 | +198 | ~18% |
| `final_integrity` | 21 | 119 | +98 | ~9% |
| `locomotion` | 13 | 55 | +42 | ~4% |
| `persistence` | ~0 | 37 | +37 (new) | ~3% |

Total delta ≈ 1096ms/tick. **The new `combat_engagement` phase was not the dominant cost** — most
of the increase (`advancement`, `resolution_overhead`, and this ticket's own `cooperation` share)
is the rest of the engine doing more real work because the world now behaves differently (more
combat -> more state changes -> more apply/hard-law-check/observability/lookup work), not a
regression in the new phase's own code. `find_pending_incoming_offer` lives inside the
`cooperation` phase's +167ms/tick share above.

## Scope
- Investigate `find_pending_incoming_offer`'s own real algorithmic complexity (is it O(n) per call,
  called once per cooperating entity per tick, or something more expensive?) and whether the
  ~2.0s/5-ticks figure generalizes beyond this one scenario (world shape, entity count, cooperation
  activity level).
- Determine whether this is inherent to what the function does (a real, unavoidable lookup cost) or
  a real optimization opportunity (missing index, redundant recomputation, etc.) — this ticket does
  not presuppose either answer.
- If a real opportunity exists, route it through the existing performance-optimization epic
  (`docs/plans/design_enhancement/performance_optimization/`) — likely M5 Gate-A evidence
  (`performance_m5_exact_optimization_delivery_epic.md`) once ranked against other contributors by
  M4's own Gate A process, not as a standalone fix decided from this one measurement.

## Out of Scope
- Any fix or optimization attempt — none was investigated, and none is authorized by this ticket.
- Re-litigating whether `ENABLE_COMBAT_ENGAGEMENT` should be enabled — that question is closed in
  its own ticket (`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`); this cost exists independent
  of that flag (the function itself is only 15% more expensive per-tick with the flag ON — see the
  A/B table — the underlying cost is present regardless).

## Acceptance Criteria
- A real investigation (not a repeat of this same ad-hoc profile) establishes whether this is
  material at realistic corpus-world scale, and if so, whether it is a real optimization candidate.
- If a candidate is confirmed, it is routed into the performance-optimization epic's own Gate-A
  process rather than fixed ad hoc.
- If it is not material at realistic scale, or the cost is inherent, that conclusion is recorded
  here and the ticket closes on that finding.

## Related Tickets
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` — where this was observed, as a side effect of
  an unrelated regression investigation.
- `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED` and
  `TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED` — two other unrelated system costs surfaced by
  the same profiling run, each its own ticket since they are independent subsystems.
- `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT` — a genuinely diagnosed defect (not a report-only
  observation) found in the same investigation, kept separate since it's a different kind of finding.

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
  ("Confirmed field evidence, 2026-09-14" — full A/B attribution table)
- `docs/plans/design_enhancement/performance_optimization/performance_m5_exact_optimization_delivery_epic.md`

## Related Code Areas
- `src/domains/cooperation/services.py::find_pending_incoming_offer`
- `src/domains/cooperation/phase.py::CooperationPhase.execute`

## Assumptions / Open Questions
- Whether 1000 entities / 50 regions / 20 buildings-per-region is representative of any real
  corpus profile this repo actually runs, or is purely a synthetic stress shape — not checked.

## Implementation Notes
_(not applicable — report-only ticket, no implementation performed)_

## Test Summary
_(not applicable — report-only ticket, no implementation performed)_

## Files Changed
_(none — report-only ticket)_

## Completion Summary
_(pending future investigation)_
