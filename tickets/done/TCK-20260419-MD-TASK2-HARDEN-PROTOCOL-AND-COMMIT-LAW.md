# TCK-20260419-MD-TASK2-HARDEN-PROTOCOL-AND-COMMIT-LAW

## Title
Milestone D - Task 2: Harden Worker Protocol and Commit Law

## Status
INPROGRESS

## Request Summary
Harden the worker protocol by implementing deterministic neighbor context, explicit work-id tracking, and a frozen priority-based commit law. Ensure authoritative equivalence between local and concurrent execution.

## Scope
- Add `work_id` to `WorkItem`, `WorkerPacket`, and `WorkerResult`.
- Implement radius-based neighbor view in `Kernel`.
- Harden `_phase_resolution` to sort results and reject duplicate entity updates.

## Out of Scope
- Redesigning the spatial indexing (using linear scan for now).
- Fallback logic hardening (Task 3).

## Acceptance Criteria
- [ ] `neighbor_view` in `WorkerPacket` is populated and sorted by `entity_id`.
- [ ] `work_id` is consistent across packet and result.
- [ ] `Kernel.py` correctly sorts results by `(class_priority, local_priority, entity_id)`.
- [ ] Duplicate entity updates in the same tick are rejected.

## Related Tickets
- `TCK-20260419-MD-TASK1-FREEZE-CONCURRENCY-CONTRACT`

## Related Docs
- `docs/engine/bounded_concurrency_contract_md.md`

## Related Code Areas
- `src_v2/core/work.py`
- `src_v2/core/worker_protocol.py`
- `src_v2/engine/kernel.py`
- `src_v2/core/protocol_validator.py`

## Implementation Notes
- Proposed 10.0 unit neighbor visibility radius.
- Enforcing Option A (One Result Per Entity).
