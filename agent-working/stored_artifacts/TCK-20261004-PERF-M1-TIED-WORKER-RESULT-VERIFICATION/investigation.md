---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Investigation: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION

## Producers and ties (read only)
- Entity results (non-zero `entity_id`): one per entity per tick. `ProtocolValidator.validate_result_batch` rejects a second one; `_phase_resolution` (`kernel.py:651`) has its own `ProtocolViolationError` guard. Key `(class_priority, -local_priority, entity_id)` is unique.
- System results (`entity_id` 0): `DRAIN_DEBT`, built synchronously by both executors from `scheduler.select_work`, which keys debt items by subsystem (one per debt key). The validator requires a `subsystem_id` but does not make system results unique per subsystem.
- Merge: `work_debt_updates[res.subsystem_id] = res.work_debt_update` (`kernel.py:648`): last writer wins, not a sum.
- Scenarios `idle`, `movement`, `resource`, `strategic` schedule one entity result per tick under the default cadence, so entity-result ties on the first two key fields need a purpose-built `ready_movers` state (twelve entities, readiness 100, `ENTITY_MOVE`).

## Experiment findings that shaped the tests
- Level 1 (ordered validated batch) differs inside a tied group by construction: the stable sort keeps arrival order. It is compared as the same results in key order; the raw order difference is asserted separately as proof the tie survives the sort.
- Refined update carries wall-clock fields (`sub_phase_costs`, metric counters named `*_ms`); they are stripped before comparing. `WorkerResult.compute_time_ns` is excluded for the same reason.
- `audit_mode=True` is required: outside it the mid-tick throttle and salience coupling read wall-clock time.

## Outcome
Bounded commutative merge rules (see the ticket and `deterministic_execution.md`). Not a unique key (ID-zero ties are real); not a defect (no shipped path diverges); the narrower-protocol bound is described but not enforced by the validator.
