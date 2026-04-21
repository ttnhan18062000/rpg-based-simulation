# Milestone 3: Contract Enforcement & Finalization [COMPLETED]

The goal of this milestone was to finalize the Town Resource Resolution by implementing a robust contract test suite. This suite ensures that the V2 engine systems (`ShopSystem`, `BlacksmithSystem`) strictly enforce the gameplay laws defined during Milestone 2, preventing invalid state transitions even if proposed by an AI.

## Proposed Changes

### [Component Name] Town Contract Tests

#### [NEW] [test_town_contract.py](file:///home/vboxuser/Work/rpg-based-simulation/tests_v2/contract/test_town_contract.py) [COMPLETED]

This file contains the contract enforcement tests for the town services.

- **Law of Value**:
    - `test_shop_sell_price_enforcement`: Verified +5 gold for wood. Correctly overrides proposed deltas.
    - `test_shop_junk_auto_sell`: Verified auto-sell logic for materials and common gear only.
- **Law of Materials**:
    - `test_blacksmith_material_consumption`: Verified consumption of 2 iron_ore + 1 wood for steel_sword.
    - `test_blacksmith_insufficient_materials`: Verified craft failure on missing materials.
    - `test_blacksmith_insufficient_gold`: Verified craft failure on missing gold.
- **Law of Knowledge**:
    - `test_blacksmith_unknown_recipe`: Verified that recipe learning precedes crafting.
    - `test_blacksmith_recipe_learning_parity`: Verified wholesale learning of all 14 recipes.

#### [Implementation Summary]
The systems are now "hardened." Any `StateUpdate` that deviates from these laws will be automatically refined or rejected by the authoritative `enforce` methods, maintaining engine truth irrespective of input quality.

## Verification Plan

### Automated Tests
- Run the new contract test suite:
  ```bash
  pytest tests_v2/contract/test_town_contract.py
  ```
- Re-run the parity test suite to ensure no regressions:
  ```bash
  pytest tests_v2/parity/test_town_resolution_parity.py
  ```

### Manual Verification
- Review the `walkthrough.md` to ensure it reflects the final "hardened" state of the engine laws.
