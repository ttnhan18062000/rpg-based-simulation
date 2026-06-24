---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-RACE-TESTS
phase: open
date: 2026-06-24
tags: [race-condition, locking, inventory, test-setup]
---

# TCK-20260624-FIX-RACE-TESTS

## Title
Fix race condition tests — entity max_slots too small for ground item quantity

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Two race condition tests fail consistently (3/3 runs — not intermittent):
- `test_race_condition_ground_item_lock`
- `test_race_condition_corpse_loot_lock`

Investigation shows the locking code at `src/engine/conservation.py:107–108` is correct — `TARGET_LOCKED` reservation exists and works. The failure is in test entity setup: `create_mock_entity()` sets `max_slots=10` but the ground item has `quantity=50 gold_coin`. With `gold_coin.stack_size=1` (default), entity 1 needs 50 inventory slots → gets `INVENTORY_FULL` before the `TARGET_LOCKED` check is ever reached. The INVENTORY_FULL return on line 100 fires first.

This is a test setup bug, not a locking bug.

## Scope
- Increase `max_slots` in `create_mock_entity()` to ≥ 100 (or reduce ground item quantity to ≤ 5 to stay within 10 slots), so the `TARGET_LOCKED` code path is actually exercised
- Verify the locking test passes and correctly demonstrates concurrent lock behavior

## Out of Scope
- Changing `conservation.py` locking logic
- Changing `InventoryService.can_add_items_with_removals()`

## Acceptance Criteria
- Both race condition tests pass consistently across 3 sequential runs
- Tests actually reach and exercise the `TARGET_LOCKED` code path (verify via assertion on `accepted=True` for the winning entity and `CONFLICT` or `TARGET_LOCKED` for the losing entity)

## Related Tickets
None

## Related Docs
- `docs/mechanics/03_economic_laws.md` — atomic conservation law

## Related Code Areas
- `tests/integration/kernel/test_race_conditions_v2.py` — `create_mock_entity()`, both test functions
- `src/engine/conservation.py:100,107–108` — `INVENTORY_FULL` check precedes `TARGET_LOCKED` check

## Assumptions / Open Questions
- Confirm `gold_coin.stack_size` in `ItemRegistry` — if it's > 1 (e.g., 50), then 50 coins fit in 1 slot and the issue is something else. Run with `--tb=long` to confirm the `INVENTORY_FULL` error message.
- Preferred fix: reduce ground item `quantity=5` to keep the test lightweight, and confirm `max_slots=10` is sufficient.

## Implementation Notes
Minimal fix in `create_mock_entity()` or at ground item creation:
```python
# Option A: increase entity capacity
entity = create_mock_entity(max_slots=100, max_weight=500.0)

# Option B: reduce item quantity
ground_item = GroundItemState(item_id="gold_coin", quantity=5, ...)
```
Option B is preferred — keeps the entity setup realistic and confirms the lock behavior with a small quantity.

## Test Summary
Run 3 times: `for i in 1 2 3; do pytest tests/integration/kernel/test_race_conditions_v2.py -v --tb=short -q 2>&1 | tail -5; done`

## Files Changed
TBD

## Completion Summary
TBD
