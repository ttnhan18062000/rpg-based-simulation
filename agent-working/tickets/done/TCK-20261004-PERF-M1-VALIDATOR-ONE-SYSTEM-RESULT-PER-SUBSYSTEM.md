---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM
phase: done
date: 2026-10-04
tags: [performance, determinism, engine]
---

# TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM

## Title
Reject a result batch that carries two system results for one subsystem, so the tied-result merge stays order-independent

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION` (PERF-M1-T04) verified the outcome
"bounded commutative merge rules". The bound is this: system results (`entity_id` 0, e.g.
`DRAIN_DEBT`) tie on the whole sort key, and the kernel merges them last-writer-wins into
`work_debt_updates[subsystem_id]`. So two results for the same subsystem with different values in
one tick make the committed state depend on arrival order. Its mutation test shows the proof digest
diverging. The shipped scheduler emits at most one `DRAIN_DEBT` item per subsystem per tick, so no
shipped path diverges today. Nothing enforces that, though:
`ProtocolValidator.validate_result_batch` (`src/core/protocol_validator.py`) accepts the duplicate.
`docs/engine/deterministic_execution.md` records "at most one system result per subsystem per tick"
as the supported protocol.

`protocol_validator.py` is one of the four files released by the owner's partial lift of the
RPG-core entry gate (2026-10-04), so this needs no gated file.

## Scope
- In `validate_result_batch`, reject a batch with more than one result carrying a
  `work_debt_update` for the same `subsystem_id`. Raise the validator's existing violation error,
  with a message that names the subsystem
- Tests:
  - the duplicate case is rejected in both arrival orders;
  - a single result per subsystem, distinct subsystems, and entity results are still accepted;
  - the T04 suite still passes. Update its mutation test so that it constructs the divergent pair
    below the validator, or asserts the new rejection. Keep proof that the instrument sees the
    divergence
- Update the system-results bullet in `docs/engine/deterministic_execution.md` from "not enforced"
  to "enforced by the validator", and update parity ledger `INFRA-420`

## Out of Scope
- `src/engine/kernel.py` (gated). The merge stays last-writer-wins; the validator makes the
  duplicate impossible
- Changing debt semantics (`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`)

## Acceptance Criteria
1. A batch with two `work_debt_update` results for one subsystem raises, whatever their order
2. Every currently valid batch shape is still accepted, which the existing validator and T04 tests
   show
3. Revert proof: removing the new check makes the duplicate test fail
4. Docs and ledger say "enforced"

## Related Tickets
- `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION` (source)
- `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`

## Related Docs
- `docs/engine/deterministic_execution.md` (tied results)
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md` (PERF-M1-T04)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION/`

## Related Code Areas
- `src/core/protocol_validator.py` (edit allowed under the partial lift)
- `src/engine/kernel.py` (read only), `tests/integration/kernel/test_tied_worker_result_order.py`

## Assumptions / Open Questions
- The validator receives the whole tick's batch at once (`kernel.py` calls `validate_result_batch(self._final_results, ...)`), so a per-batch check covers one tick

## Implementation Notes
- `ProtocolValidator.validate_result_batch` (`src/core/protocol_validator.py`) now tracks `seen_debt_subsystems` and raises `ProtocolViolationError("Duplicate system result for subsystem <id>")` when a second result with a `work_debt_update` and a `subsystem_id` arrives for one subsystem. The check mirrors the kernel's own merge condition (`work_debt_update is not None and subsystem_id`), so a system result without a debt update is not counted. The batch is the whole tick's results (`kernel.py` and the concurrent executor both validate the full list), so one batch is one tick.
- Shipped producers: nothing shipped emits two debt updates for one subsystem. Evidence is the real-tick suites below, which run the validator on every tick's actual results (the scheduler emits one `DRAIN_DEBT` item per debt key).
- T04: the characterisation test that said the validator accepts the pair is flipped to `test_validator_rejects_two_system_results_for_one_subsystem`. The mutation test stays meaningful: it injects the divergent pair inside `_phase_resolution`, below collection-time validation, so the instrument still shows the proof digest diverging (its docstring says so).
- Docs and ledger: the "bound" bullet in `docs/engine/deterministic_execution.md` and `INFRA-420` now say "enforced". Schema ratchet unchanged for the entry (0 errors).

## Test Summary
- New `tests/unit/core/test_protocol_validator_system_results.py` (6 tests): the duplicate is rejected in either order for different and equal values, and with other results between the pair; one system result, distinct subsystems, entity plus system, and an empty batch are still accepted; a system result without a debt update is not counted.
- Red first: the 4 duplicate tests failed with `DID NOT RAISE` before the change.
- Revert proof (AC3): with the check removed, 5 tests fail with `DID NOT RAISE` (the new duplicate tests plus the flipped T04 test).
- Real-tick evidence (AC2): `test_worker_integrity`, `test_worker_harden`, `test_worker_determinism`, the whole T04 module (26 tests, local/thread/process routes), `test_executor_determinism`, `test_concurrency_parity` and `tests/docs`: 125 passed, 2 skipped, 1 xfailed in 81 s.

## Files Changed
- `src/core/protocol_validator.py` (allowed under the partial lift; no gated file)
- `tests/unit/core/test_protocol_validator_system_results.py` (new), `tests/integration/kernel/test_tied_worker_result_order.py`
- `docs/engine/deterministic_execution.md`, `docs/parity_ledger/infrastructure.yaml`, `docs/REGISTRY.yaml`

## Completion Summary
The validator now rejects a second debt-update system result for one subsystem in a tick, which makes the tied-result merge order-independent by construction. Nothing shipped emitted such a pair: the real-tick worker, executor, tied-result and parity suites pass (125 passed). Docs and `INFRA-420` say "enforced".
