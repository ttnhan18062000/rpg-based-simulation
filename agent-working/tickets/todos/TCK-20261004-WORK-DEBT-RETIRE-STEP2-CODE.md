---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE
phase: open
date: 2026-10-04
tags: [performance, engine]
---

# TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE

## Title
Work-debt retirement step 2: remove `work_debt` and the branches that can never fire

## Status
BLOCKED

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
On 2026-10-04 the owner chose to retire work debt, in two steps
(`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`). No producer is to be built: "overflowed
work" has no deterministic definition, and feeding wall-clock-driven shedding into it would break
PERF-D1 A1. This is step 2. It removes the field and every branch that can only ever see 0. It
touches gated files, so it is BLOCKED until the RPG-core entry gate lifts.

## Scope
The reader list is in the investigation ticket, AC2. Remove:
- `AuthoritativeState.work_debt` (`state.py`), with its canonical-hash entry (`checkpoint.py`
  `data["work_debt"]`). This changes the proof digest's input, so it needs a scheme-version
  decision under PERF-D5 (for example `flat-sha256-v2`) and a baseline note
- `StateUpdate.work_debt_updates` and the `apply.py` clamp
- the kernel's `work_debt_updates` merge and `debt_ratio`
- the debt half of `global_salience`. Coordinate with `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`:
  if that fix lands first, it removes the salience term entirely
- the governor and phase_governor debt thresholds and recovery limit, and the `work_debt_total`
  signal
- the `DRAIN_DEBT` scheduler, executor and validator path, including the per-subsystem rule from
  #319. Update the T04 analysis in `deterministic_execution.md`
- `max_work_debt` in the profiles, `PressureInjector.inject_work_debt`, and the
  `WORK_DEBT_BUILDUP` certification scenario
- reporting surfaces: API, snapshot, Prometheus `sim_work_debt_total`, certification model, the
  root-cause rule
- Replace the guard test `test_work_debt_stays_empty_in_production.py` with a test that the field
  is gone
- **Added 2026-10-06 (owner decision, option (c) of `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`):**
  the same PERF-D5 scheme bump also removes the never-wired periodic/opportunistic shedding path. That
  means: `state.periodic_due_ticks` (hashed, `checkpoint.py` about 116) and `StateUpdate.periodic_updates`
  (no producer), `PeriodicDefinition` and the periodic branch of `DeterministicScheduler.select_work`
  (unless a real task has been registered by then), the empty `allow_opportunistic` branch, and the
  unread `diagnostic_verbosity` / `metrics_detail` policy fields. It also fixes two misleading comments,
  `src/engine/observability.py:32` and `src/core/governance.py:45`: the counter counts only scheduler
  drops. Update the mechanism tests that register test-only periodic definitions (`test_degradation_order`,
  `test_scheduler_contract`, `test_work_classes`, `test_signal_truth`, `test_deferred_work_debt`, the
  work-debt guard) to match. The evidence is in that ticket's stored investigation.

## Out of Scope
- Any producer, or any new deferred-work design (PERF-D3: needs its own feature contract)

## Acceptance Criteria
1. `git grep -n work_debt -- src` is empty, or each remaining reference is listed with a reason
2. Proof digest scheme versioned, with a baseline / replay compatibility note
3. Governor mode behaviour is unchanged on non-combat runs (it never read a non-zero value)
4. Docs, parity ledger and the Prometheus metric list are updated

## Related Tickets
- `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`, `TCK-20261004-WORK-DEBT-RETIRE-STEP1-DOCS`
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`, `TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM`

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3, PERF-D5)
- `docs/engine/deterministic_execution.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION/`

## Related Code Areas
- `src/core/state.py`, `src/engine/apply.py`, `src/engine/kernel.py`, `src/engine/governor.py` (all gated)
- `src/engine/phase_governor.py`, `src/engine/scheduler.py`, `src/engine/executor.py`,
  `src/core/protocol_validator.py`, `src/engine/checkpoint.py`, `src/certification/`, `src/config/profiles.py`

## Assumptions / Open Questions
- BLOCKED by the RPG-core entry gate (it edits gated core files). Code-health gates are blocking
  from 2026-10-18, so run `make code-health` and `make typecheck-py` before the PR

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
