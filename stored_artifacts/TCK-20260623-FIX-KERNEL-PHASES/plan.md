# Plan — TCK-20260623-FIX-KERNEL-PHASES

## Summary

Two test-only fixes. No production code changes.

Files changed:
1. `tests/integration/kernel/test_milestone_a_closure.py:78` — change source inspection target
2. `tests/integration/kernel/test_race_conditions_v2.py:62` — replace ItemStack with GroundItemState

## Root Cause 1: Source inspection targets wrong method

`test_milestone_a_closure.py:78` calls `inspect.getsource(Kernel.tick_once)` and asserts
`_phase_init` appears in the source. But `tick_once` is a thin wrapper; actual phase calls
live in `_tick_once_inner`. Fix: change `Kernel.tick_once` → `Kernel._tick_once_inner`.

## Root Cause 2: Test fixture uses wrong type

`test_race_conditions_v2.py:62` builds `AuthoritativeState(ground_items={100: ItemStack("gold_coin", 50)})`.
`ground_items` requires `Dict[int, GroundItemState]`, not `ItemStack`. `GroundItemState` has `.position`;
`ItemStack` does not. `world_index.py:151` accesses `.position`, causing AttributeError.

Fix: replace with `GroundItemState(id=100, item_id="gold_coin", quantity=50, position=(5.0, 5.0))`.

## Parity Ledger

No production behavior changed — no ledger update required.

## Test Commands

```bash
pytest tests/integration/kernel/test_milestone_a_closure.py -x -q
pytest tests/integration/kernel/test_race_conditions_v2.py -x -q
pytest tests/integration/kernel/ tests/unit/kernel/ -q --tb=no
```
