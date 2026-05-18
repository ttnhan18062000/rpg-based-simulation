import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

"""Data-integrity contract tests for NPC Spawn Configs and Loadouts."""

import pytest
from src_legacy.core.models.enums import EnemyTier
from src_legacy.core.world.spawn_config import SPAWN_CONFIGS

# These tests verify that the dynamic data loading from SPAWN_CONFIGS (or equivalent maps)
# matches the expected game design contracts.
@pytest.mark.parametrize("race, tier, expected_gear_subset", [
    ("bandit", EnemyTier.BASIC, ["bandit_dagger"]),
    ("bandit", EnemyTier.SCOUT, ["bandit_bow"]),
    ("bandit", EnemyTier.ELITE, ["hunting_bow", "chainmail"]),
    ("undead", EnemyTier.BASIC, ["rusty_sword"]),
    ("undead", EnemyTier.SCOUT, ["wooden_staff"]),
    ("undead", EnemyTier.WARRIOR, ["iron_sword"]),
    ("undead", EnemyTier.ELITE, ["apprentice_staff"]),
    # Note: Orcs are likely loaded too, but I will focus on verified ones
    ("wolf", EnemyTier.ELITE, []), # Wolves generally have no gear in this config
])
def test_npc_loadout_integrity(race, tier, expected_gear_subset):
    """Verify that specific NPC tiers are assigned their canonical equipment."""
    from src_legacy.core.world.spawn_config import SPAWN_CONFIGS
    config = SPAWN_CONFIGS.get((race, tier))
    
    assert config is not None, f"NPC {race} T{tier} config missing from SPAWN_CONFIGS"
    for item in expected_gear_subset:
        assert item in config.starting_gear, f"NPC {race} T{tier} config missing gear {item}"

@pytest.mark.parametrize("race, tier, expected_kind", [
    ("bandit", EnemyTier.BASIC, "bandit"),
    ("bandit", EnemyTier.SCOUT, "bandit_archer"),
    ("bandit", EnemyTier.ELITE, "bandit_chief"),
    ("undead", EnemyTier.BASIC, "skeleton"),
    ("undead", EnemyTier.SCOUT, "skeleton_mage"),
    ("undead", EnemyTier.WARRIOR, "lich"),
    ("undead", EnemyTier.ELITE, "wraith"),
    ("wolf", EnemyTier.BASIC, "wolf"),
    ("wolf", EnemyTier.SCOUT, "dire_wolf"),
    ("wolf", EnemyTier.WARRIOR, "alpha_wolf"),
    ("wolf", EnemyTier.ELITE, "warg"),
])
def test_npc_kind_mapping_integrity(race, tier, expected_kind):
    """Verify that race/tier combinations map to the correct semantic kind name."""
    from src_legacy.core.gameplay.items.items import RACE_TIER_KINDS
    kind = RACE_TIER_KINDS.get(race, {}).get(tier)
    assert kind == expected_kind, f"Mapping {race} T{tier} should be {expected_kind}, got {kind}"
