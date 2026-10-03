---
status: active
artifact_type: test_plan
ticket_id: TCK-20260623-FIX-INVENTORY-DEFAULTS
date: 2026-06-23
tags: [inventory, max_slots, test-plan]
---

# Test Plan — TCK-20260623-FIX-INVENTORY-DEFAULTS

## Scope

Verify that:
1. The production default `max_slots = 16` is correctly in place and consistent with docs.
2. The D10 F4 named tests pass (confirmed passing at investigation time).
3. No test regresses on the corrected docs.

This test plan does NOT cover the 32 pipeline regression failures in
`tests/unit/resource/` — those are a separate regression (pipeline `InteractionUpdate`
emission) tracked separately.

---

## Test Commands

### 1. Confirm D10 F4 named tests pass

Run the four tests D10 F4 flagged as failing:

```bash
python3 -m pytest \
  tests/unit/resource/test_inventory_serialization.py::test_inventory_limits \
  tests/unit/resource/test_durability_repair.py::TestCraftingCapacity::test_crafting_succeeds_with_freed_space \
  tests/unit/resource/test_inventory_hardening.py \
  tests/integration/pipeline/test_transaction_completion.py -k "insufficient_gold" \
  -v --tb=short
```

Expected: all pass.

### 2. Confirm inventory serialization suite

```bash
python3 -m pytest tests/unit/resource/test_inventory_serialization.py -v --tb=short
```

Expected: 3 passed.

### 3. Confirm inventory hardening suite

```bash
python3 -m pytest tests/unit/resource/test_inventory_hardening.py -v --tb=short
```

Expected: 3 passed.

### 4. Confirm item inventory contract

```bash
python3 -m pytest tests/unit/resource/test_item_inventory_contract.py -v --tb=short
```

Expected: passes.

### 5. Confirm quest tests that document the new default

```bash
python3 -m pytest \
  tests/unit/quest/test_progression_lifecycle.py \
  tests/unit/quest/test_quest_transactions.py \
  tests/unit/quest/test_transaction_groups.py \
  -v --tb=short
```

Expected: all pass (these tests already comment `# V2 builder default max_slots is 16`).

### 6. Targeted default-value smoke test

Run all tests that explicitly check `max_slots` value after construction without setting it:

```bash
python3 -m pytest tests/unit/resource/ tests/unit/quest/ tests/integration/pipeline/ \
  -k "inventory" --tb=short -q
```

### 7. Post-docs-fix: knowledge index update

After updating `docs/core/items_and_inventory.md`, run:

```bash
make knowledge-index-update
```

---

## Out of Scope

- `tests/unit/resource/test_resource_conservation_regression.py` — fails due to pipeline
  `AuthoritativeApplyPipeline` regression (not default value). Excluded from this ticket.
- `tests/unit/resource/test_resource_contract.py` — same pipeline regression. Excluded.
- Full resource suite (`pytest tests/unit/resource/`) — currently 32 failures from pipeline
  regression. Do not run as pass gate for this ticket.

---

## Pass Gate

This ticket is complete when:
- [ ] All 6 commands above produce 0 failures
- [ ] `docs/core/items_and_inventory.md` §3 shows `max_slots: int = 16` and `max_weight: float = 50.0`
- [ ] `make knowledge-index-update` completes without error
