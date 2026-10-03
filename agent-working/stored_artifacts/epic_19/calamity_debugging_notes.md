---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [epic_19]
---

# Calamity System Debugging Notes

## Final Resolution Summary

The Calamity System and core Item system have been fully restored and stabilized. All 53 tests in `test_ranged_combat.py` and all 3 tests in `test_calamity_system.py` are passing.

### Key Fixes

1. **Circular Dependency Resolution**
   - Migrated `ITEM_REGISTRY` and `ItemTemplate` to a standalone module: `src/core/item_registry.py`.
   - Updated all core modules (`models.py`, `buildings.py`, `generator.py`, `world_loop.py`) to import from the new registry module.
   - Refactored `src/core/items.py` to re-export moved components, maintaining backwards compatibility while breaking the circular import cycle.

2. **Item System Restoration**
   - Reconstructed critical constants in `src/core/items.py` that were accidentally purged during refactoring:
     - `RACE_TIER_KINDS`: Mappings for entity evolution.
     - `RACE_STARTING_GEAR`: Class/Race specific equipment.
     - `RACE_STAT_MODS`: Balanced multipliers for different races.
     - `TIER_KIND_NAMES` and `TIER_STARTING_GEAR`: Global defaults for tiered spawns.
   - Restored missing `bandit` and `undead` equipment expected by the combat test suite.

3. **Data-Driven Registry Fixes**
   - Migrated legendary boss weapons (`gorath_cleaver`, `vexira_fang`) from code to `data/items.json`.
   - This ensures they are correctly loaded during registry initialization, allowing the `auto_equip_best` logic to function correctly for World Bosses.

4. **Quest System Enhancement**
   - Added `force_template_id` support to `generate_quest`.
   - Updated `WorldLoop._check_calamity_spawns` to explicitly trigger the `calamity_hunter` bounty quest for all heroes when a World Boss appears.

### Verification Results

| Test Suite | Result | Notes |
| :--- | :--- | :--- |
| `tests/test_calamity_system.py` | **PASSED** | Verifies boss stats, spawning, and bounty quest assignment. |
| `tests/test_ranged_combat.py` | **PASSED** | Verifies weapon ranges, line of sight, and tier-specific gear. |

## Recommendations for Future Work
- **Registry Guarding**: Consider adding validation to `ITEM_REGISTRY` to prevent accidental clearing during runtime if static items are expected to persist.
- **Data Validation**: Implement a schema check for `items.json` to ensure all required fields (like `weapon_range`) are present for all items.
