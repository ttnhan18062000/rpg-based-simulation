# Restoring Data-Integrity & Contract Tests

The user noted a drop in test count and asked if the missing tests are "still needed." My audit shows that the removed tests were largely **Data Integrity checks** (verifying ranges in `items.json` and NPC gear assignments).

While the core combat logic is still tested, the **data contract** for 20+ weapons and 15+ NPCs is currently unverified. Typos in the JSON data could lead to silent bugs (e.g., an archer with a range of 1).

This plan details how to restore this coverage using a "lean" parametrized approach.

## User Review Required

> [!IMPORTANT]
> I recommend restoring the tests for **Data Integrity** because the game loads items/NPCs from JSON. A single typo in `items.json` could break a specific weapon's range without being caught by generalized logic tests.

## Proposed Changes

### 1. Item Registry Contract Tests
I will add a new test file focused on verifying the loaded data from `items.json`.

#### [NEW] [test_item_contracts.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/core/gameplay/test_item_contracts.py)
- **Parametrized Weapon Ranges**: Verify the `weapon_range` for all 20+ items in the registry against their expected values.
- **Parametrized Stat Bonuses**: Ensure core weapons (Windpiercer, etc.) have their secondary stats (SPD, CRIT) correctly mapped from data.

### 2. NPC Loadout Verification
I will verify that all NPC templates have the correct gear assigned.

#### [MODIFY] [test_ranged_combat.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/combat/test_ranged_combat.py)
- Add a parametrized loop for all **EnemyTier** and **Race** combinations to ensure they are assigned the correct starting weapon (e.g., Bandit Archer must have a bow).

### 3. LOS Edge Case Restoration
I will restore the 10+ specific LOS edge cases (walls on diagonals, etc.) which were lost during the move.

## Verification Plan

### Automated Tests
- Run `pytest --collect-only` and verify count returns to ~1360+.
- Run `pytest tests/unit/core/gameplay/test_item_contracts.py` to verify the new registry checks.

### Manual Verification
- None.
