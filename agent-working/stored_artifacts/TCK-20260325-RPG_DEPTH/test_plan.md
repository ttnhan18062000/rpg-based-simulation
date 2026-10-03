---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260325-RPG_DEPTH
artifact_type: test_plan
tags: [rpg_depth]
---

# Test Plan - TCK-20260325-RPG_DEPTH

## Unit Tests
- `tests/unit/core/test_attribute_synergy.py`:
  - `test_luck_affects_crit`: Verify crit rate increases significantly with luck.
  - `test_cha_affects_familiarity`: Verify familiarity rate scales with charisma.
  - `test_per_discovery`: Verify hidden entities are invisible without enough PER.
- `tests/unit/core/test_class_weighting.py`:
  - `test_warrior_prefers_sword`: Verify Warrior chooses high-ATK over high-MATK.
  - `test_mage_prefers_staff`: Verify Mage chooses high-MATK over high-ATK.
- `tests/unit/ai/test_inn_buff.py`:
  - `test_well_rested_application`: Verify buff applies after town rest.

## Manual Verification
- View simulation logs to see "Well-Rested" buff applied to heroes leaving town.
- Observe "Hero-Slayer" monsters dropping better loot for high-luck heroes.
