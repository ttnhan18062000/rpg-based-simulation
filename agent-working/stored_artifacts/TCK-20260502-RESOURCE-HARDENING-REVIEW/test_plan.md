---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260502-RESOURCE-HARDENING-REVIEW
artifact_type: test_plan
tags: [resource, hardening, review]
---

# Test Plan: Resource Hardening Review

## New Tests
- `tests/engine/test_resource_conflicts.py`:
    - `test_contested_corpse_loot`: Two actors try to loot same corpse in same tick.
    - `test_contested_harvest`: Two actors try to harvest same node in same tick.
    - `test_contested_ground_item`: Two actors try to pick up same ground item.
- `tests/engine/test_transaction_grouping.py`:
    - `test_non_contiguous_grouping`: Verify intents with same `group_id` are grouped even if separated.
    - `test_group_atomic_rollback`: Verify whole group fails if one intent fails.

## Regression Tests
- `pytest tests/rpg/test_rpg_depth.py`
- `pytest tests/engine/test_hardening_e5.py`

## Validation Scripts
- `python3 scripts/ledger_validator.py`
- `python3 scripts/release_gate.py`
