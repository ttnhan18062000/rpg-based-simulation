---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260427-PHASE3-RESOURCE-CONSERVATION
artifact_type: test_plan
tags: [phase3, resource, conservation]
---

# Test Plan: Phase 3 Resource Conservation

## Regression Tests (Legacy Port)
- Port `tests_legacy/rpg/test_resource_conservation.py` to `tests/rpg/test_resource_conservation.py`.
- Ensure it fails with the current `src/` implementation.

## New Characterization Tests
- **Harvest Full Inventory**: Verify that harvesting a node with a full inventory resets the interaction but DOES NOT deplete the node.
- **Loot Ground Item Full Inventory**: Verify that picking up a ground item with a full inventory resets the interaction but DOES NOT remove the ground item.
- **Loot Corpse Full Inventory**: Verify that looting a corpse with a full inventory resets the interaction but DOES NOT remove the corpse.
- **Partial Capacity Check**: Verify that if an entity can only accept 2 out of 5 items, the entire operation is rejected (all-or-nothing conservation law).

## Integration Tests
- Run `tests/inventory/test_harvest_channeling.py` and `tests/inventory/test_loot_channeling.py` to ensure no regression in normal channeling.

## Verification Commands
```bash
pytest tests/rpg/test_resource_conservation.py
pytest tests/inventory/test_harvest_channeling.py
pytest tests/inventory/test_loot_channeling.py
```
