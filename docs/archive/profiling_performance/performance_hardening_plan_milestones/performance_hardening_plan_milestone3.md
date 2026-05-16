# Milestone 3 — Add O(Dirty) vs O(N) Reference Parity

## Goal

Prove that optimized dirty-path behavior produces the same semantic result as the full scan reference path.

DirtySet is a performance optimization. It must never define truth.

## Design

Add a debug/reference mode:

```text
optimized mode:
    systems consume dirty_set

reference mode:
    same systems scan all relevant entities/world objects
```

Then compare final canonical state.

## Tasks

| Task                                                   | Narrow implementation logic                                                                                             | Files / area                 |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| M3.1 Add execution flag                                | Add `force_full_scan=True` / `disable_dirty_optimization=True`.                                                         | runtime/profile/test harness |
| M3.2 Implement full-scan branch for DirtySet consumers | Strategic, Group, Shop, CapacityEnforcement must support full scan in test mode.                                        | systems                      |
| M3.3 Build canonical comparison helper                 | Use existing state hashing/diff helper. Existing tests already include state diff logic around `CanonicalStateHasher`.  | tests helper                 |
| M3.4 Compare final state after N ticks                 | Run optimized and full-scan from same seed/state.                                                                       | tests                        |
| M3.5 Compare intermediate dirty decisions              | Optional audit: record processed entity IDs and verify optimized subset is semantically sufficient.                     | diagnostics                  |

## New tests to add

```python
def test_dirty_optimized_vs_full_scan_idle_parity_100_ticks():
    ...

def test_dirty_optimized_vs_full_scan_movement_parity_100_ticks():
    ...

def test_dirty_optimized_vs_full_scan_resource_parity_100_ticks():
    ...

def test_dirty_optimized_vs_full_scan_combat_parity_100_ticks():
    ...

def test_dirty_optimized_vs_full_scan_strategic_parity_100_ticks():
    ...

def test_dirty_optimized_vs_full_scan_mixed_parity_250_ticks():
    ...
```

## Acceptance checklist

```text
[ ] A full-scan reference mode exists.
[ ] O(Dirty) mode and O(N) mode produce identical canonical final state.
[ ] Parity tests cover idle, movement, resource, combat, strategic, and mixed scenarios.
[ ] Parity tests run for more than 1 tick.
[ ] Any intentional divergence is documented with a reason and test.
```

## Exit condition

Dirty optimization becomes proven, not assumed.

---
