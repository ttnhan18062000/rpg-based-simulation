# TCK-20260428-RESOURCE-QUEST-TRANSACTIONS

## Title

Implement Transactional Quest Rewards (Phase 3.1)

## Status

DONE

## Request Summary

Migrate and harden quest reward logic from legacy to V2, ensuring quest status changes are transactional and tied to successful reward delivery.

## Scope

- Implement `ResourceTransactionResolver` integration for quest rewards.
- Ensure quest status `REWARDED` is only set after successful resource transfer.
- Implement pending reward handling if inventory is full.
- Add tests for quest reward transactions.

## Out of Scope

- Multi-transfer semantics (Task 3.2) - unless naturally unified.
- Non-inventory progression (XP) separation (Task 1.1) - unless necessary for 3.1.

## Acceptance Criteria

- [ ] Quest reward transaction resolves first.
- [ ] Quest status changes to `REWARDED` only after accepted transfer.
- [ ] Rejected reward keeps quest in `COMPLETED` or `REWARD_PENDING`.
- [ ] Test: full inventory blocks quest reward and does not mark rewarded.
- [ ] Test: after freeing inventory, pending reward can complete.

## Related Tickets

- None

## Related Docs

- [resource_v2_e3_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e3_phases.md)
- [logic_checklist_exhaustive_v2.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive_v2.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/quests/service.py`
- `src/engine/resource_transaction_resolver.py` (assumed name based on phases doc)
- `tests/quests/test_quest_transactions.py` [NEW]

## Assumptions / Open Questions

- Does `ResourceTransactionResolver` already exist in `src/engine/`?
- How is "pending reward" currently represented in the state?

## Implementation Notes

- To be updated during work.

## Test Summary

- To be updated.

## Files Changed

- To be updated.

## Completion Summary

- To be updated.
