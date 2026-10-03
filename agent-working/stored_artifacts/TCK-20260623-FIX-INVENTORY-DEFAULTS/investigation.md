---
status: active
artifact_type: investigation
ticket_id: TCK-20260623-FIX-INVENTORY-DEFAULTS
date: 2026-06-23
tags: [inventory, max_slots, defaults, parity, docs]
---

# Investigation — TCK-20260623-FIX-INVENTORY-DEFAULTS

## Summary

The D10 audit (F4) flagged "Inventory capacity defaults diverged" with 13 claimed failing
tests. Investigation reveals the situation is more nuanced: the `max_slots` default **was**
changed from 8 → 16, but the tests named by D10 **already pass** in isolation. The real
failures in the resource suite (32 tests) are a separate, deeper pipeline regression
unrelated to the default value. What remains is a **docs parity gap**: one doc still
documents the old value.

---

## 1. Production Default (Source of Truth)

**File:** `src/core/models/inventory.py:44`

```python
@dataclass(frozen=True, slots=True)
class InventoryComponent:
    items: List[ItemStack] = field(default_factory=list)
    gold: int = 0
    max_slots: int = 16       # <-- current production default
    max_weight: float = 50.0
```

**Compliance ID:** TOWN-013

**Changed in:** commit `56211688` ("Resource V2 Implementation") — `max_slots: int = 8`
→ `max_slots: int = 16`.

---

## 2. Documentation State

| Source | Value | Status |
|---|---|---|
| `src/core/models/inventory.py` | **16** | Authoritative — current |
| `docs/mechanics/03_economic_laws.md` §2 Slot Limit | **16** | Already updated — in parity |
| `docs/core/items_and_inventory.md` §3 Inventory Class | **8** | **STALE — diverged** |
| `tests/helpers/presets.py:122` helper default | **10** | Explicit override, not a default assertion |

The `docs/core/items_and_inventory.md` code block still shows the legacy V1 `Inventory`
class (not `InventoryComponent`) with `max_slots: int = 8`. This is a stale legacy doc
excerpt — the class definition itself is V1 and was replaced wholesale.

---

## 3. Test Default Assertions — What D10 Claimed vs Reality

D10 F4 asserted these 4 tests were failing due to default mismatch:

| Test | D10 claim | Actual current status |
|---|---|---|
| `test_inventory_limits` (serialization) | expects 5 slots, gets 10 | **PASSES** — test explicitly sets `max_slots=2`, no default assertion |
| `test_inventory_hardening` | expects 2 items at limit, gets 3 | **PASSES** — test explicitly sets `max_slots=2` |
| `test_crafting_succeeds_with_freed_space` | `INVENTORY_FULL` raised unexpectedly | **PASSES** in isolation |
| `test_insufficient_gold_records_reason` (integration/pipeline) | `INVENTORY_FULL` instead of `INSUFFICIENT_GOLD` | **PASSES** in isolation |

All 6 tests run together: `6 passed, 20 deselected in 0.30s`

**Conclusion:** The D10 F4 inventory default failures were already fixed before this ticket
was opened. None of the 4 named tests assert the raw default value — they all pass explicit
`max_slots` values in test fixtures.

---

## 4. Actual Failing Tests in Resource Suite

Running `pytest tests/unit/resource/` shows **32 failures**, but they are NOT default-value
failures. The failure patterns are:

| Pattern | Count | Root cause |
|---|---|---|
| `AttributeError: 'NoneType' object has no attribute 'reset'` | ~8 | `e_upd.interaction` is `None` — pipeline no longer emits `InteractionUpdate` on capacity block |
| `AttributeError: 'NoneType' object has no attribute 'items_add'` | ~2 | `e_upd.inventory` is `None` — pipeline emits no inventory update |
| `KeyError: 1` on `refined.entity_updates[1]` | ~6 | Pipeline emits no `EntityUpdate` for entity 1 at all |
| Unrelated economy/shop logic failures | ~16 | Different root cause (shop/crafting pipeline regression) |

These are `AuthoritativeApplyPipeline.refine()` behavioral regressions — the pipeline
stopped emitting expected `InteractionUpdate(reset=True)` when inventory is full during
harvest/loot. These fall outside the scope of TCK-20260623-FIX-INVENTORY-DEFAULTS.

---

## 5. Parity Ledger

**TOWN-013** (`docs/parity_ledger/town_resource.yaml:137`):
- `status: verified`
- `text: Inventory state tracks both slots and weight/carry burden.`
- Does not enumerate the specific default value of `max_slots`.
- No update required for this entry.

The parity ledger does not have a discrete entry for `max_slots default = 16`. One should
be added if this ticket scope expands to cover parity ledger hardening.

---

## 6. Recommendation

This is **not a production bug**. The default `max_slots = 16` is intentional (V2 design),
confirmed by:
- `docs/mechanics/03_economic_laws.md` §2: "Default: **16 slots**"
- `src/certification/scenarios.py` using `max_slots=10` as an explicit lower bound for
  tests (not relying on default)
- Test comments: `# V2 builder default max_slots is 16` in
  `tests/unit/quest/test_progression_lifecycle.py:21`

**Remaining work for this ticket:**
1. Update `docs/core/items_and_inventory.md` §3 to replace the stale V1 `Inventory` class
   code block with the current `InventoryComponent` definition showing `max_slots: int = 16`
   and `max_weight: float = 50.0`.
2. The 32 resource suite pipeline failures are a separate regression (pipeline no longer
   emits `InteractionUpdate`/`InventoryUpdate` on capacity block). They should be tracked
   in a separate ticket.

---

## 7. Files with Implicit Reliance on Default (No Explicit max_slots)

These call `InventoryComponent()` or `V2EntityBuilder(...).inventory(...)` without
`max_slots` — they implicitly get 16:

- `src/core/state.py:672` — `EntityState.inventory` field default
- `src/core/state.py:1023` — `TownState.inventory` field default
- `src/cognition/self_assessment.py:101` — fallback `getattr(inv, "max_slots", 20)`
  (uses 20 as sentinel, not 16 — minor inconsistency but not load-bearing)
- `src/world/providers/requirements.py:104` — fallback `getattr(..., "max_slots", 16)`
  — correctly uses 16 as sentinel

No implicit reliance in tests (all test fixtures set `max_slots` explicitly or use the
builder which flows through to `InventoryComponent`).
