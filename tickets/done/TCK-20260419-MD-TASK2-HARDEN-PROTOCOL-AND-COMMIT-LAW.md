---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260419-MD-TASK2-HARDEN-PROTOCOL-AND-COMMIT-LAW
phase: done
date: 2026-04-19
tags: [md, task2, harden, protocol, and, commit, law]
---

# TCK-20260419-MD-TASK2-HARDEN-PROTOCOL-AND-COMMIT-LAW

## Title
Milestone D - Task 2: Harden Worker Protocol and Commit Law

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

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
- `src/core/work.py`
- `src/core/worker_protocol.py`
- `src/engine/kernel.py`
- `src/core/protocol_validator.py`

## Implementation Notes
- Proposed 10.0 unit neighbor visibility radius.
- Enforcing Option A (One Result Per Entity).
