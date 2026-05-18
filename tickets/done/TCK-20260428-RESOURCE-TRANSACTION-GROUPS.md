# TCK-20260428-RESOURCE-TRANSACTION-GROUPS

## Title

Multi-Transfer Transaction Semantics (Atomic Groups)

## Status

DONE

## Request Summary

Implement support for grouping `ResourceTransferIntent` objects into atomic "all-or-nothing" transaction groups.

## Scope

- Add `group_id` and `is_group_required` to `ResourceTransferIntent`.
- Implement group-aware resolution in `AuthoritativeApplyPipeline._resolve_resource_transactions`.
- Add rollback logic for failed group members.
- Add comprehensive tests for atomic success and failure.

## Acceptance Criteria

- [ ] Multiple intents with the same `group_id` succeed or fail together.
- [ ] Failure of a required intent rolls back all previous successes in the same group in that tick.
- [ ] Non-grouped intents continue to resolve independently.
- [ ] Tests prove rollback on inventory failure and other rejection reasons.

## Related Tickets

- [TCK-20260428-RESOURCE-QUEST-TRANSACTIONS](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260428-RESOURCE-QUEST-TRANSACTIONS.md)

## Related Docs

- [resource_v2_e3_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e3_phases.md) (Task 3.2)

## Related Code Areas

- [src/core/updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- [src/engine/pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
