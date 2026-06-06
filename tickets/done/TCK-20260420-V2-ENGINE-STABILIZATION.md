# TCK-20260420-V2-ENGINE-STABILIZATION

## Title
V2 Resource Engine Test Stabilization and Protocol Alignment

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Resolve all failing tests in `tests/` following the Milestone C/D architecture hardening.

## Scope
- Fix protocol-stripping bug in `WorkerManager`.
- Align `WorkerPacket` and `WorkerResult` signatures in tests.
- Enforce system-reserved ID 0 by shifting actor IDs to start from 1.
- Reconcile `capacity_utilization` with the disaggregated `worker_utilization` / `queue_utilization` schema.
- Align `manifest.json` with code terminology.

## Out of Scope
- Implementing new RPG domain logic (Movement slice is already implemented).
- Distributed worker architecture.

## Acceptance Criteria
- [x] 100% pass rate in `pytest tests/` (156 items).
- [x] No `ProtocolViolationError` related to entity_id 0 collisions.
- [x] All telemetry tests use disaggregated signals.
- [x] Manifest terminology aligns with `src/certification/models.py`.

## Related Tickets
- None

## Related Docs
- [resource_handbook.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_handbook.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/worker_manager.py`
- `src/core/worker_protocol.py`
- `tests/`

## Assumptions / Open Questions
- None

## Implementation Notes
- Discovered that `WorkerManager._wrap_work` was manually reconstructing `WorkerResult` without preserving `subsystem_id`, which was causing protocol violations in high-pressure scenarios.

## Test Summary
- Ran `pytest tests/`: 156/156 PASSED.

## Files Changed
- `src/engine/worker_manager.py`
- `tests/engine/test_signal_truth.py`
- `tests/engine/test_worker_integrity.py`
- `tests/engine/test_worker_adaptation.py`
- `tests/engine/test_worker_determinism.py`
- `tests/engine/test_local_executor.py`
- `tests/engine/test_milestone_b_closure.py`
- `tests/engine/test_milestone_d_closure.py`
- `tests/engine/test_observability_budgets.py`
- `tests/certification/test_envelope_violations.py`
- `tests/certification/test_harness_contract.py`

## Completion Summary
Full test suite stability restored. The V2 engine is now compliant with all declared Milestone C/D/E laws.
