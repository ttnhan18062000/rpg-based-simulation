# Plan — TCK-20260623-FIX-INVENTORY-DEFAULTS

## Summary

D10 F4 is already resolved — the 4 named tests pass (they explicitly set max_slots in fixtures).
Production default is max_slots=16 (correct per V2 design, docs/mechanics/03_economic_laws.md §2).

One doc fix needed:
- `docs/core/items_and_inventory.md` §3 has a stale V1 `Inventory` class snippet showing `max_slots: int = 8`; update to show current `InventoryComponent` with `max_slots: int = 16`

Separate regression (out of scope):
- 32 resource suite failures are from `AuthoritativeApplyPipeline.refine()` no longer emitting
  `InteractionUpdate(reset=True)` when inventory is full. This is a separate pipeline behavioral
  regression requiring its own ticket.

## No test changes required.

## Test Commands

```bash
pytest tests/unit/resources/ -q --tb=no  # shows 32 pre-existing failures (pipeline regression)
pytest tests/unit/core/test_inventory_limits.py tests/unit/core/test_inventory_hardening.py -q
```
