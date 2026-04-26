# Test Plan - Resource Conservation Hardening

## Goal
Prove that world resources (nodes, corpses, ground items) are never depleted if the actor's inventory cannot accept the items.

## Test Cases

### 1. Harvest Conservation
- Setup: A resource node with 1 charge. A hero with 1 slot filled.
- Action: Hero completes harvest.
- Expected:
    - Node charge remains 1.
    - Hero inventory remains the same.
    - Interaction reset.

### 2. Loot Conservation (Corpse)
- Setup: A corpse with items. A hero with full inventory.
- Action: Hero completes looting.
- Expected:
    - Corpse remains in state.
    - Hero inventory remains the same.

### 3. Pickup Conservation (Ground Item)
- Setup: A ground item. A hero with full inventory.
- Action: Hero completes pickup.
- Expected:
    - Ground item remains in state.
    - Hero inventory remains the same.

## Tools
- `pytest`
- Custom test harness in `tests/systems/test_resource_conservation_regression.py`.
