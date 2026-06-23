---
ticket_id: TCK-20260623-FIX-KERNEL-PHASES
date: 2026-06-23
status: complete
---

# Investigation: TCK-20260623-FIX-KERNEL-PHASES

## Root Cause 1 — Kernel `_phase_init` not visible in `tick_once` source

### Confirmed: YES

**Test**: `tests/integration/kernel/test_milestone_a_closure.py::test_final_kernel_law_compliance` (line 60–80)

**Mechanism**: The test calls `inspect.getsource(Kernel.tick_once)` and asserts that each of the 6 mandated phase names (including `_phase_init`) appears in the returned source string. However, the kernel was refactored to split the tick body into two methods:

- `tick_once()` (lines 278–293): thin wrapper that sets a thread-local flag and calls `self._tick_once_inner()`
- `_tick_once_inner()` (lines 295–): the actual phase orchestrator containing all `_phase_*` calls

`_phase_init` is called correctly at `src/engine/kernel.py:299` inside `_tick_once_inner`, and the method itself is defined at line 423. The method exists; the wiring is correct. Only the test's source-inspection target is wrong.

**Exact failure**:
```
AssertionError: Kernel.tick_once does not orchestrate mandated phase: _phase_init
assert '_phase_init' in '    def tick_once(self) -> None:\n        ...\n            self._tick_once_inner()\n        ...'
```

**Doc note**: `docs/engine/kernel.md` describes a **7-phase** loop (Init, Scheduling, Collection, Resolution, Cleanup, Advancement, Persistence) but the ticket text says "6-phase". The test checks 6 phases (excluding Persistence). The kernel contract is for 7; the test is checking for 6 specifically named phase methods. This is a pre-existing doc/test minor mismatch but not the root cause of the failure.

### Fix Plan for RC1

**Option A (preferred — minimal scope, preserves architecture)**: Change the test at `tests/integration/kernel/test_milestone_a_closure.py:78` to inspect `_tick_once_inner` instead of `tick_once`:

```python
# Before:
source = inspect.getsource(Kernel.tick_once)
# After:
source = inspect.getsource(Kernel._tick_once_inner)
```

This is the correct fix because the architecture deliberately separates the hot-path guard wrapper (`tick_once`) from the body (`_tick_once_inner`). The test should verify that the body orchestrates all phases, not the wrapper.

**Option B (more invasive — not recommended)**: Inline `_tick_once_inner` back into `tick_once`. This would require restructuring the hot-path guard try/finally block and is a larger change with more risk.

**Files to change**: `tests/integration/kernel/test_milestone_a_closure.py` line 78 only.

---

## Root Cause 2 — `ItemStack` used where `GroundItemState` is required

### Confirmed: YES

**Error site**: `src/engine/world_index.py:151`

```python
# _build_ground_item_index, line 148-153:
for g_id, g in state.ground_items.items():
    pos = (int(g.position[0]), int(g.position[1]))   # line 151 — AttributeError here
```

**Expected type**: `state.ground_items` is typed `Dict[int, GroundItemState]`. `GroundItemState` (defined at `src/core/state.py:940`) has a `position: tuple[float, float]` field.

**Actual object at runtime**: `ItemStack` (defined at `src/core/models/inventory.py:24`), which has fields `item_id`, `quantity`, `properties` — no `position`.

**Root cause**: The race conditions test populates `ground_items` with an `ItemStack` directly:

```python
# tests/integration/kernel/test_race_conditions_v2.py:62
state = AuthoritativeState(
    tick=1, seed=1, entities={1: e1, 2: e2},
    ground_items={100: ItemStack("gold_coin", 50)}  # WRONG — should be GroundItemState
)
```

`AuthoritativeState` is a frozen dataclass and does not enforce the value type at construction time (Python generics are not runtime-checked). The `ItemStack` is accepted silently, then crashes when `_build_ground_item_index` tries to access `.position` on it.

**Cascade**: This error fires whenever `WorldIndexService.get_indexes(state)` is called on any state whose `ground_items` contains `ItemStack` objects. This cascades into all tests that call into the pipeline or kernel with this malformed state.

**What `GroundItemState` requires**:
```python
# src/core/state.py:940
@dataclass(frozen=True, slots=True)
class GroundItemState:
    id: int
    item_id: str
    quantity: int
    position: tuple[float, float]
```

### Fix Plan for RC2

**Fix location**: `tests/integration/kernel/test_race_conditions_v2.py:62`

Replace `ItemStack("gold_coin", 50)` with a proper `GroundItemState`:

```python
# Before:
from src.core.state import ..., ItemStack, ...
state = AuthoritativeState(
    tick=1, seed=1, entities={1: e1, 2: e2},
    ground_items={100: ItemStack("gold_coin", 50)}
)

# After:
from src.core.state import ..., GroundItemState, ...
state = AuthoritativeState(
    tick=1, seed=1, entities={1: e1, 2: e2},
    ground_items={100: GroundItemState(id=100, item_id="gold_coin", quantity=50, position=(5.0, 5.0))}
)
```

The `ResourceTransferIntent` at lines 64–65 references `source_id=100, source_kind="GROUND_ITEM"` — the `id` field in `GroundItemState` must match `source_id=100`. Position `(5.0, 5.0)` is arbitrary for the race condition test since the test only cares about lock contention semantics, not spatial position.

**Files to change**: `tests/integration/kernel/test_race_conditions_v2.py` line 62 only (import + construction).

---

## Out-of-Scope Failures Observed

The following failures were detected in test runs but are NOT caused by RC1 or RC2. They are independent bugs:

| Test | Failure | Root cause (observed, not investigated) |
|---|---|---|
| `test_milestone_b_operational_gate` | `SURVIVAL != DEGRADED` | Governor mode transition thresholds or tick budget mock values |
| `test_milestone_c_desimulation` (×2) | Debt counter mismatch | Desimulation debt accumulation logic |
| `test_milestone_d_closure` | `(2.0, 0.0) != (2.0, 0.0)` | Floating point comparison or position swap rounding |
| `test_mutation_boundary_*` (7 tests) | `ent_ref is None` after refine | TrustBoundaryPhase.strip() returning empty entity_updates |
| `test_movement_micro_arena_*` (4 tests) | `KeyError: 1` in entity_updates | Movement pipeline not producing updates |
| `test_position_swap_*` (3 tests) | `KeyError: 1` in entity_updates | Same as above |
| `test_tactical_movement` (3 tests) | `combat is None` / `new_position is None` | Movement/combat phase not producing expected updates |

These are noted for awareness but are out of scope for this ticket per the ticket's "Scope" and "Out of Scope" sections.

---

## Risks

1. **RC1 fix (test change)**: Low risk. Changing `getsource(Kernel.tick_once)` to `getsource(Kernel._tick_once_inner)` is a pure test assertion correction. The kernel implementation is already correct.

2. **RC2 fix (test data fix)**: Low risk. Replacing `ItemStack` with `GroundItemState` in test data is a correction of a test setup error. No production code changes. The `items_add` fields in the `ResourceTransferIntent` at lines 64–65 still use `ItemStack` correctly — only the `ground_items` dict value needs to change.

3. **Milestone B/C/D and pipeline failures**: These are separate bugs. Fixing RC1 and RC2 as described will not resolve them. The ticket's acceptance criteria include tests that may still fail due to these independent issues. This should be flagged to the ticket author before marking done.
