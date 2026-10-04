---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION
phase: open
date: 2026-10-04
tags: [performance, engine, bug]
---

# TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION

## Title
`AuthoritativeState.work_debt` has no production writer that increases it, so every debt-driven signal is permanently zero

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by perf-planner on 2026-10-04 while reviewing `TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS`,
at `origin/main` `9793aee08`. The ticket's implementer could not make debt accumulate through the
kernel and had to seed it. perf-planner traced every writer:

- `AuthoritativeState.work_debt: Dict[str, int]` (`src/core/state.py:1423`) changes only in
  `apply.py` (around line 323), as `max(0, prior + delta)` over `StateUpdate.work_debt_updates`.
- The kernel fills `work_debt_updates` only from `WorkerResult.work_debt_update`
  (`src/engine/kernel.py`, around line 647).
- The only producer of `work_debt_update` is the executor's `DRAIN_DEBT` branch
  (`src/engine/executor.py`, around lines 192 and 338). It sets it to
  `SimulationDomainLogic.drain_debt()`, which returns `-profile.max_worker_count`. That value is
  always negative or zero.
- The scheduler emits `DRAIN_DEBT` only for systems already in `state.work_debt`
  (`src/engine/scheduler.py`, around line 124).
- Dropped work is recorded in `RuntimeStatus` counters (`record_dropped_work`), not in
  `state.work_debt`.
- The only code that increases it is `src/certification/scenarios.py::inject_work_debt`, which is
  test and certification scaffolding.

So in ordinary play `work_debt` starts empty and stays empty. Everything derived from it is
constant zero:
- the governor's `work_debt_total` and its debt-based mode thresholds and recovery limit
  (`governor.py`, `phase_governor.py`);
- the kernel's `debt_ratio`;
- the work-debt term of `global_salience`.

This matters for `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`. That fix keeps the work-debt
term and removes the compute term, so after it lands `global_salience` is always 0 in production,
and the salience price multiplier is always 1.

PERF-D3 (closed) says capacity debt is the aggregate counter. The counter exists, but no production
path produces debt. Either a producer was lost or never built, or the dropped-work counter was
meant to be the debt.

## Scope
- Confirm the trace with a test: a long run of each non-combat perf scenario at a tight profile
  (dropped work recorded) ends with empty `state.work_debt`
- Find the intent: search git history and docs (`docs/engine/contracts/resource_governor_contract.md`,
  the Milestone C notes behind `drain_debt`) for where debt was meant to be produced
- Recommend one of:
  - wire a deterministic producer (PERF-D1 A1: no wall-clock input);
  - retire `work_debt` and the dead governor branches;
  - document it as certification-only.

  The recommendation goes to the owner as a decision, not an implementation

## Out of Scope
- Implementing the producer or the retirement. That needs an owner decision, and the files
  involved (`kernel.py`, `apply.py`, `governor.py`, `state.py`) are gated
- The salience fix itself (RPG-core track)

## Acceptance Criteria
1. A test shows `state.work_debt` stays empty across real runs in which dropped work is non-zero
2. The ticket lists every reader of `work_debt` and says which behaviour is dead because of it
3. A recommendation (producer, retire, or certification-only) with evidence is recorded in the ticket and sent to perf-planner for the owner; the decision itself is out of scope

## Related Tickets
- `TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS` (where it was found)
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (its remaining salience term is this zero)
- `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION` (the kernel's `work_debt_updates[...] =` is last-writer-wins for tied system results)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3, PERF-D1)
- `docs/engine/contracts/resource_governor_contract.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `src/core/state.py`, `src/engine/apply.py`, `src/engine/kernel.py`, `src/engine/executor.py`,
  `src/engine/scheduler.py`, `src/engine/domain_logic.py`, `src/engine/governor.py`,
  `src/engine/phase_governor.py`, `src/certification/scenarios.py`

## Assumptions / Open Questions
- **Owner decision 2026-10-04: investigate first.** This ticket now runs as investigation only, under the partial lift: the confirming test (AC1), the reader list (AC2), and a history/doc search for the intended producer. No `src/` edit at all. AC3 becomes: a written recommendation (producer / retire / certification-only), with evidence, put to the owner. The chosen change is a separate ticket that waits for the gate if it touches gated files
- This trace is a code read plus a keyword search, not a proof. The confirming test is AC1

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
